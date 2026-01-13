from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from embeddings.embedder import get_embedding_model


def build_faiss_index(documents: List[Document]):
    embedding_model = get_embedding_model()

    vectorstore = FAISS.from_documents(
        documents=documents,
        embedding=embedding_model
    )

    return vectorstore
