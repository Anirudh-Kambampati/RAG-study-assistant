from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader


def load_docx(path: str) -> List[Document]:
    loader = Docx2txtLoader(path)
    return loader.load()
