from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
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

    return merged
