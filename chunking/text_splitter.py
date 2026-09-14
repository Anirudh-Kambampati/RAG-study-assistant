from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",   # paragraphs (DOCX)
            "\n",     # bullets (PPTX)
            ". ",
            " ",
            ""
        ],
    )

    chunks = splitter.split_documents(documents)

    # ---- Merge small chunks (for PPTX) ----
    merged = []
    buffer = ""

    for doc in chunks:
        text = doc.page_content.strip()

        if len(text) < 200:
            buffer += " " + text
        else:
            if buffer:
                doc.page_content = buffer + " " + text
                buffer = ""
            merged.append(doc)

    if buffer and merged:
        merged[-1].page_content += buffer
    elif buffer:
        # Every chunk was small enough to buffer and none was ever big
        # enough to flush into `merged` (e.g. a short document) — without
        # this, the leftover buffer, and thus the entire document, would be
        # silently dropped instead of producing at least one chunk.
        last_metadata = chunks[-1].metadata if chunks else {}
        merged.append(Document(page_content=buffer.strip(), metadata=last_metadata))

    return merged
