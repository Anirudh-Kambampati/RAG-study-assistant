"""Qdrant vector-store module.

All Qdrant-specific logic (client setup, collection config, payload shape,
filtering, MMR re-ranking) lives here so api/main.py never talks to the
Qdrant SDK directly. One collection (`metis_documents`) holds every user's
every document's chunks; isolation between users/documents is enforced by
payload filters on every read and write, never left to the caller.
"""

import os
import uuid
from typing import List, Tuple

import numpy as np
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from embeddings.embedder import get_embedding_model

COLLECTION_NAME = "metis_documents"

_client: QdrantClient | None = None
_embedding_dim: int | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        if not url:
            raise RuntimeError("QDRANT_URL is not set")
        _client = QdrantClient(url=url, api_key=api_key)
    return _client


def _embedding_dimension() -> int:
    """The embedding model's actual output size, determined by embedding a
    throwaway string rather than hardcoded — stays correct if the model
    backing get_embedding_model() ever changes."""
    global _embedding_dim
    if _embedding_dim is None:
        sample = get_embedding_model().embed_query("dimension probe")
        _embedding_dim = len(sample)
    return _embedding_dim


def create_collection_if_missing() -> None:
    client = get_qdrant_client()
    if client.collection_exists(COLLECTION_NAME):
        return
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=_embedding_dimension(),
            # The previous FAISS index (FAISS.from_documents' default
            # DistanceStrategy.EUCLIDEAN_DISTANCE) used Euclidean/L2
            # distance — matched here so retrieval semantics don't
            # silently change when swapping backends.
            distance=qmodels.Distance.EUCLID,
        ),
    )
    # Every read/write is filtered on these two fields; indexing them keeps
    # that filtering fast instead of degrading to a full collection scan as
    # metis_documents grows across users.
    client.create_payload_index(COLLECTION_NAME, "user_id", qmodels.PayloadSchemaType.KEYWORD)
    client.create_payload_index(COLLECTION_NAME, "doc_id", qmodels.PayloadSchemaType.KEYWORD)


def _owner_filter(user_id: str, doc_id: str) -> qmodels.Filter:
    """The single filter every retrieval/delete/count goes through — scoped
    to BOTH user and document, so one user can never reach another user's
    vectors, nor even another one of their own documents by accident."""
    return qmodels.Filter(
        must=[
            qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id)),
            qmodels.FieldCondition(key="doc_id", match=qmodels.MatchValue(value=doc_id)),
        ]
    )


def upsert_document_chunks(user_id: str, doc_id: str, filename: str, chunks: List[Document]) -> int:
    """Embed and upsert one document's chunks. Returns the number of points
    written. Caller should only mark the document "indexed" once this
    returns successfully."""
    create_collection_if_missing()
    embedder = get_embedding_model()
    vectors = embedder.embed_documents([c.page_content for c in chunks])

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        payload = dict(chunk.metadata or {})
        payload.update(
            {
                "user_id": user_id,
                "doc_id": doc_id,
                "filename": filename,
                "chunk_id": i,
                "text": chunk.page_content,
            }
        )
        points.append(qmodels.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload))

    client = get_qdrant_client()
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def document_exists(user_id: str, doc_id: str) -> bool:
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return False
    result = client.count(collection_name=COLLECTION_NAME, count_filter=_owner_filter(user_id, doc_id), exact=True)
    return result.count > 0


def search_document(
    user_id: str,
    doc_id: str,
    query_embedding: List[float],
    k: int,
    fetch_k: int,
    lambda_mult: float = 0.5,
) -> List[Tuple[Document, float]]:
    """MMR search scoped to one user's one document.

    Fetches `fetch_k` nearest candidates (with vectors) restricted to
    (user_id, doc_id) via a Qdrant payload filter, then re-ranks them with
    the exact same `maximal_marginal_relevance` utility the previous FAISS
    path used (FAISS's own MMR method calls this same function internally)
    — so the diversity re-ranking behavior is identical, not just similar.
    """
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return []

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=_owner_filter(user_id, doc_id),
        limit=fetch_k,
        with_payload=True,
        with_vectors=True,
    )
    candidates = response.points
    if not candidates:
        return []

    embedding_list = [c.vector for c in candidates]
    mmr_indices = maximal_marginal_relevance(
        np.array(query_embedding),
        embedding_list,
        lambda_mult=lambda_mult,
        k=min(k, len(candidates)),
    )

    selected: List[Tuple[Document, float]] = []
    for idx in mmr_indices:
        point = candidates[idx]
        payload = dict(point.payload or {})
        text = payload.pop("text", "")
        selected.append((Document(page_content=text, metadata=payload), point.score))
    return selected


def delete_document(user_id: str, doc_id: str) -> None:
    """Delete every vector belonging to one user's one document. A no-op
    (not an error) if the collection or the document has no vectors."""
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=qmodels.FilterSelector(filter=_owner_filter(user_id, doc_id)),
    )
