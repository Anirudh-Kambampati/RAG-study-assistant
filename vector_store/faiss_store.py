from typing import List
from pathlib import Path
import hashlib

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from embeddings.embedder import get_embedding_model


BASE_INDEX_DIR = "faiss_index"


def _source_to_dir(source: str) -> Path:
    # hash the source to avoid path issues
    source_hash = hashlib.md5(source.encode()).hexdigest()
    return Path(BASE_INDEX_DIR) / source_hash


def build_and_save_faiss_index(documents: List[Document], source: str):
    embedding_model = get_embedding_model()
    index_dir = _source_to_dir(source)

    vectorstore = FAISS.from_documents(
        documents=documents,
        embedding=embedding_model
    )

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(index_dir)

    return vectorstore


def load_faiss_index(source: str):
    embedding_model = get_embedding_model()
    index_dir = _source_to_dir(source)

    return FAISS.load_local(
        index_dir,
        embedding_model,
        allow_dangerous_deserialization=True
    )


def index_exists(source: str) -> bool:
    return _source_to_dir(source).exists()
