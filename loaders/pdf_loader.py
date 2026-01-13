from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf(path: str) -> List[Document]:
    loader = PyPDFLoader(path)
    return loader.load()
