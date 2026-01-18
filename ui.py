import streamlit as st
import tempfile

from loaders.loader_factory import load_source
from chunking.text_splitter import split_documents
from vector_store.faiss_store import build_and_save_faiss_index
from chat_utils import load_chats, save_chats


st.set_page_config(page_title="New Chat", layout="wide")
st.title("📄 RAG Study Assistant ")
st.subheader("➕ Create a new chat")

# Load existing chats from disk
chats = load_chats()

st.subheader("Upload a document")

upload = st.file_uploader(
    "Supported formats: PDF, DOCX, PPTX, TXT",
    type=["pdf", "docx", "pptx", "txt"],
    accept_multiple_files=False,
)

if upload:
    doc_id = upload.name

    # If chat already exists
    if doc_id in chats:
        st.warning("A chat already exists for this document. Open it from Chats page.")
        st.stop()

    # Save uploaded file to disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{upload.name}") as tmp:
        tmp.write(upload.read())
        file_path = tmp.name

    # Build vector index
    with st.spinner("Indexing document (one-time process)..."):
        documents = load_source(file_path)
        chunks = split_documents(documents)
        build_and_save_faiss_index(chunks, doc_id)

    # Create chat entry
    chats[doc_id] = {
        "messages": [],
        "index_dir": f"faiss_index/{doc_id}"
    }

    save_chats(chats)

    st.success("Chat created successfully!")
    st.info("Go to the Chats page to open it.")
