from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredPowerPointLoader


def load_pptx(path: str) -> List[Document]:
    loader = UnstructuredPowerPointLoader(path)
    return loader.load()
