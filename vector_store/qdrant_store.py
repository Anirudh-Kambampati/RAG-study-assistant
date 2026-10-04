"""Qdrant vector-store module.

All Qdrant-specific logic (client setup, collection config, payload shape,
filtering, hybrid search, MMR re-ranking) lives here so api/main.py never
talks to the Qdrant SDK directly. One collection (`metis_documents`) holds
every user's every document's chunks; isolation between users/documents is
enforced by payload filters on every read and write, never left to the
caller.

Retrieval is hybrid: each chunk gets a dense embedding (semantic similarity)
and a sparse BM25-style embedding (lexical/keyword match, via fastembed's
"Qdrant/bm25" model — no extra ML model download beyond a small ONNX
tokenizer, no external API). A query fetches candidates from both and lets
Qdrant fuse them server-side with Reciprocal Rank Fusion, so an exact term
(a formula, a name, a number) that dense embeddings alone sometimes rank low
still surfaces. MMR re-ranking then runs on top of the fused pool exactly as
before, for diversity.
"""

import os
import uuid
from typing import List, Tuple

import numpy as np
from fastembed import SparseTextEmbedding
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from embeddings.embedder import get_embedding_model

COLLECTION_NAME = "metis_documents"
# Qdrant requires sparse vectors to be named (dense stays the collection's
# single unnamed/default vector) — this name just has to be consistent
# between upsert and search.
SPARSE_VECTOR_NAME = "bm25"

_client: QdrantClient | None = None
_embedding_dim: int | None = None
_sparse_embedder: SparseTextEmbedding | None = None


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


def _get_sparse_embedder() -> SparseTextEmbedding:
    global _sparse_embedder
    if _sparse_embedder is None:
        _sparse_embedder = SparseTextEmbedding(model_name="Qdrant/bm25")
    return _sparse_embedder


def create_collection_if_missing() -> None:
    client = get_qdrant_client()
    sparse_config = {SPARSE_VECTOR_NAME: qmodels.SparseVectorParams()}

    if client.collection_exists(COLLECTION_NAME):
        # Qdrant does not support adding a new sparse vector space to an
        # already-existing collection (confirmed directly against the API —
        # it 400s) — only new named *dense* vectors can be added that way.
        # A collection created before hybrid search existed has to be
        # dropped and recreated; there's no in-place migration path.
        info = client.get_collection(COLLECTION_NAME)
        if not info.config.params.sparse_vectors or SPARSE_VECTOR_NAME not in info.config.params.sparse_vectors:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' predates hybrid search and has no "
                f"'{SPARSE_VECTOR_NAME}' sparse vector space. Qdrant can't add one in "
                "place — delete the collection (client.delete_collection) and let it "
                "be recreated, re-uploading any documents you need to keep."
            )
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
        sparse_vectors_config=sparse_config,
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
    """Embed (dense + sparse) and upsert one document's chunks. Returns the
    number of points written. Caller should only mark the document "indexed"
    once this returns successfully."""
    create_collection_if_missing()
    texts = [c.page_content for c in chunks]
    dense_vectors = get_embedding_model().embed_documents(texts)
    # `passage_embed` (not `query_embed`) applies BM25's full term-frequency
    # saturation — the right side for indexed documents vs. the query side.
    sparse_vectors = list(_get_sparse_embedder().passage_embed(texts))

    points = []
    for i, (chunk, dense_vec, sparse_vec) in enumerate(zip(chunks, dense_vectors, sparse_vectors)):
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
        points.append(
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "": dense_vec,
                    SPARSE_VECTOR_NAME: qmodels.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist(),
                    ),
                },
                payload=payload,
            )
        )

    client = get_qdrant_client()
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def document_exists(user_id: str, doc_id: str) -> bool:
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return False
    result = client.count(collection_name=COLLECTION_NAME, count_filter=_owner_filter(user_id, doc_id), exact=True)
    return result.count > 0


def count_document_chunks(user_id: str, doc_id: str) -> int:
    """Total chunk count for one user's one document — lets the caller decide
    whether the whole document reasonably fits in one prompt (see
    get_all_document_chunks) instead of narrowing via similarity search."""
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return 0
    result = client.count(collection_name=COLLECTION_NAME, count_filter=_owner_filter(user_id, doc_id), exact=True)
    return result.count


def get_all_document_chunks(user_id: str, doc_id: str) -> List[Document]:
    """Every chunk of one user's one document, in original document order
    (sorted by chunk_id) rather than similarity order. For questions that
    need the whole document (e.g. "summarize this"), retrieving the top-k
    most-similar-to-the-query chunks systematically misses whatever isn't
    near the query embedding — returning everything sidesteps that when the
    document is small enough for it to be practical (see caller for the
    size threshold)."""
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return []

    points: list = []
    next_offset = None
    while True:
        batch, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=_owner_filter(user_id, doc_id),
            limit=100,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )
        points.extend(batch)
        if next_offset is None:
            break

    points.sort(key=lambda p: (p.payload or {}).get("chunk_id", 0))

    docs = []
    for point in points:
        payload = dict(point.payload or {})
        text = payload.pop("text", "")
        docs.append(Document(page_content=text, metadata=payload))
    return docs


def search_document(
    user_id: str,
    doc_id: str,
    query_text: str,
    k: int,
    fetch_k: int,
    lambda_mult: float = 0.5,
) -> List[Tuple[Document, float]]:
    """Hybrid (dense + BM25) search scoped to one user's one document, then
    MMR re-ranked for diversity.

    Fetches `fetch_k` candidates from a dense nearest-neighbor search and
    `fetch_k` from a sparse BM25 search (both restricted to (user_id,
    doc_id) via the same owner filter), fuses them server-side with
    Reciprocal Rank Fusion, then re-ranks the fused pool with the exact same
    `maximal_marginal_relevance` utility the previous dense-only path used
    (FAISS's own MMR method calls this same function internally) — so a
    document's exact wording (a formula, a name, a number) that the dense
    embedding alone might rank low can still surface, while the final
    diversity behavior is unchanged.
    """
    client = get_qdrant_client()
    if not client.collection_exists(COLLECTION_NAME):
        return []

    dense_query = get_embedding_model().embed_query(query_text)
    sparse_query = list(_get_sparse_embedder().query_embed([query_text]))[0]
    owner_filter = _owner_filter(user_id, doc_id)

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            qmodels.Prefetch(query=dense_query, using="", filter=owner_filter, limit=fetch_k),
            qmodels.Prefetch(
                query=qmodels.SparseVector(
                    indices=sparse_query.indices.tolist(),
                    values=sparse_query.values.tolist(),
                ),
                using=SPARSE_VECTOR_NAME,
                filter=owner_filter,
                limit=fetch_k,
            ),
        ],
        query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
        query_filter=owner_filter,
        limit=fetch_k,
        with_payload=True,
        with_vectors=True,
    )
    candidates = response.points
    if not candidates:
        return []

    # Each candidate's dense vector lives under the unnamed "" key since the
    # collection has both a default dense space and a named sparse one.
    embedding_list = [c.vector[""] for c in candidates]
    mmr_indices = maximal_marginal_relevance(
        np.array(dense_query),
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
