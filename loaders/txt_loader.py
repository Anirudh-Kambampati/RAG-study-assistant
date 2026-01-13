from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader


def load_txt(path: str) -> List[Document]:
    loader = TextLoader(path)
    return loader.load()
