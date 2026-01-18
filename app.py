from loaders.loader_factory import load_source
from chunking.text_splitter import split_documents
from vector_store.faiss_store import (
    build_and_save_faiss_index,
    load_faiss_index,
    index_exists,
)
from llm.generator import get_llm


# ---- Dynamic input ----
source = input("Enter file path or URL: ").strip()

# ---- Indexing / loading ----
if not index_exists(source):
    print("Building new index...")
    documents = load_source(source)
    chunks = split_documents(documents)
    vectorstore = build_and_save_faiss_index(chunks, source)
else:
    print("Loading existing index...")
    vectorstore = load_faiss_index(source)

# ---- Query loop ----
llm = get_llm()

while True:
    query = input("\nAsk a question (or 'exit'): ").strip()
    if query.lower() == "exit":
        break

    docs = vectorstore.similarity_search(query, k=3)
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)

    prompt = f"""
You are a strict question-answering assistant.

Use ONLY the information present in the context below.
If the answer is not contained in the context, say:
"I don’t know based on the provided document."

Context:
{context}

Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)
    print("\nAnswer:\n")
    print(response)
