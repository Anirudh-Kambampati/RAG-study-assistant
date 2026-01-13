from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader


def load_html(source: str) -> List[Document]:
    loader = WebBaseLoader(source)
    return loader.load()
