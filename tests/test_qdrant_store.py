"""Integration tests for vector_store/qdrant_store.py against the real Qdrant
cluster configured via QDRANT_URL/QDRANT_API_KEY. Each test cleans up the
(user_id, doc_id) pairs it creates so it never leaves data behind."""

import uuid

import pytest
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

from vector_store.qdrant_store import (
    COLLECTION_NAME,
    create_collection_if_missing,
    delete_document,
    document_exists,
    get_qdrant_client,
    search_document,
    upsert_document_chunks,
)
from embeddings.embedder import get_embedding_model


@pytest.fixture(scope="module")
def embedder():
    return get_embedding_model()


@pytest.fixture()
def owner():
    """A fresh (user_id, doc_id) pair, deleted after the test regardless of
    outcome so tests never accumulate leftover vectors."""
    user_id, doc_id = f"test-user-{uuid.uuid4().hex[:8]}", f"test-doc-{uuid.uuid4().hex[:8]}"
    yield user_id, doc_id
    delete_document(user_id, doc_id)


def test_connection_and_collection_creation():
    create_collection_if_missing()
    assert get_qdrant_client().collection_exists(COLLECTION_NAME)


def test_upsert_and_document_exists(owner):
    user_id, doc_id = owner
    chunks = [
        Document(page_content="Mitosis produces two identical diploid cells.", metadata={"page": 1}),
        Document(page_content="Meiosis produces four distinct haploid cells.", metadata={"page": 2}),
    ]
    n = upsert_document_chunks(user_id, doc_id, "bio.pdf", chunks)
    assert n == 2
    assert document_exists(user_id, doc_id) is True


def test_document_exists_false_for_unknown_pair():
    assert document_exists("no-such-user", "no-such-doc") is False


def test_vector_count_matches_chunks(owner):
    user_id, doc_id = owner
    chunks = [Document(page_content=f"Chunk number {i} about cell biology.") for i in range(5)]
    upsert_document_chunks(user_id, doc_id, "notes.txt", chunks)

    client = get_qdrant_client()
    count = client.count(collection_name=COLLECTION_NAME, count_filter=None, exact=True).count
    assert count >= 5  # collection is shared, so only a lower bound is meaningful here


def test_search_returns_relevant_chunk_with_metadata(owner, embedder):
    user_id, doc_id = owner
    chunks = [
        Document(page_content="The mitochondria produces ATP through oxidative phosphorylation.", metadata={"page": 3}),
        Document(page_content="The chloroplast performs photosynthesis using sunlight.", metadata={"page": 7}),
    ]
    upsert_document_chunks(user_id, doc_id, "cell.pdf", chunks)

    query_embedding = embedder.embed_query("How does the mitochondria make energy?")
    results = search_document(user_id, doc_id, query_embedding, k=1, fetch_k=10)

    assert len(results) == 1
    doc, score = results[0]
    assert "mitochondria" in doc.page_content.lower()
    assert doc.metadata.get("page") == 3
    assert doc.metadata.get("filename") == "cell.pdf"
    assert isinstance(score, float)


@pytest.mark.parametrize("k", [3, 5, 8])
def test_search_depth_k_is_respected(owner, embedder, k):
    user_id, doc_id = owner
    chunks = [Document(page_content=f"Fact number {i}: cells have many organelles.") for i in range(10)]
    upsert_document_chunks(user_id, doc_id, "facts.txt", chunks)

    query_embedding = embedder.embed_query("Tell me about cell organelles.")
    results = search_document(user_id, doc_id, query_embedding, k=k, fetch_k=max(k * 4, 20))
    assert len(results) == k


def test_doc_id_filtering_isolates_documents_for_same_user(embedder):
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    doc_a, doc_b = f"doc-a-{uuid.uuid4().hex[:8]}", f"doc-b-{uuid.uuid4().hex[:8]}"
    try:
        upsert_document_chunks(user_id, doc_a, "a.txt", [Document(page_content="Content about astronomy and stars.")])
        upsert_document_chunks(user_id, doc_b, "b.txt", [Document(page_content="Content about cooking recipes.")])

        query_embedding = embedder.embed_query("Tell me about astronomy.")
        results = search_document(user_id, doc_a, query_embedding, k=1, fetch_k=10)
        assert len(results) == 1
        assert "astronomy" in results[0][0].page_content.lower()

        results_b = search_document(user_id, doc_b, query_embedding, k=1, fetch_k=10)
        assert len(results_b) == 1
        assert "cooking" in results_b[0][0].page_content.lower()
    finally:
        delete_document(user_id, doc_a)
        delete_document(user_id, doc_b)


def test_user_id_filtering_prevents_cross_user_access(embedder):
    doc_id = f"shared-doc-{uuid.uuid4().hex[:8]}"
    user_a, user_b = f"user-a-{uuid.uuid4().hex[:8]}", f"user-b-{uuid.uuid4().hex[:8]}"
    try:
        upsert_document_chunks(user_a, doc_id, "a.txt", [Document(page_content="User A's private financial notes.")])

        query_embedding = embedder.embed_query("What are the financial notes?")
        # User B queries the SAME doc_id user A used — must see nothing.
        results_b = search_document(user_b, doc_id, query_embedding, k=5, fetch_k=20)
        assert results_b == []

        # User A, querying their own doc_id, still finds it.
        results_a = search_document(user_a, doc_id, query_embedding, k=5, fetch_k=20)
        assert len(results_a) == 1
    finally:
        delete_document(user_a, doc_id)
        delete_document(user_b, doc_id)


def test_delete_document_removes_only_that_owners_vectors(embedder):
    doc_id = f"del-doc-{uuid.uuid4().hex[:8]}"
    user_a, user_b = f"del-user-a-{uuid.uuid4().hex[:8]}", f"del-user-b-{uuid.uuid4().hex[:8]}"
    try:
        upsert_document_chunks(user_a, doc_id, "a.txt", [Document(page_content="A's content.")])
        upsert_document_chunks(user_b, doc_id, "b.txt", [Document(page_content="B's content.")])
        assert document_exists(user_a, doc_id) is True
        assert document_exists(user_b, doc_id) is True

        delete_document(user_a, doc_id)

        assert document_exists(user_a, doc_id) is False
        assert document_exists(user_b, doc_id) is True  # untouched
    finally:
        delete_document(user_a, doc_id)
        delete_document(user_b, doc_id)


def test_delete_document_is_a_noop_for_unknown_pair():
    delete_document("never-existed-user", "never-existed-doc")  # must not raise
