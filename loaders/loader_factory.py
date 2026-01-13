from typing import List
from langchain_core.documents import Document
from pathlib import Path

from loaders.pdf_loader import load_pdf
from loaders.docx_loader import load_docx
from loaders.pptx_loader import load_pptx
from loaders.txt_loader import load_txt
from loaders.html_loader import load_html


def load_source(source: str) -> List[Document]:
    if source.startswith("http://") or source.startswith("https://"):
        return load_html(source)

    ext = Path(source).suffix.lower()

    if ext == ".pdf":
        return load_pdf(source)
    elif ext == ".docx":
        return load_docx(source)
    elif ext == ".pptx":
        return load_pptx(source)
    elif ext == ".txt":
        return load_txt(source)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
