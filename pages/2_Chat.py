import streamlit as st

from vector_store.faiss_store import load_faiss_index
from llm.generator import get_llm
from chat_utils import load_chats, save_chats


st.set_page_config(page_title="Chat", layout="wide")

# Safety check
if "active_doc" not in st.session_state:
    st.error("No chat selected. Go to the Chats page.")
    st.stop()

doc_id = st.session_state.active_doc

# Load chats from disk
chats = load_chats()

if doc_id not in chats:
    st.error("Chat not found.")
    st.stop()

messages = chats[doc_id]["messages"]

# Load vector DB (already built earlier)
vectorstore = load_faiss_index(doc_id)

st.title(f"💬 Chat — {doc_id}")
st.divider()

# -------------------------------
# Render previous messages
# -------------------------------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------------
# Chat input
# -------------------------------
user_query = st.chat_input("Ask something about the document")

if user_query:
    # Store user message
    messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            docs = vectorstore.similarity_search(user_query, k=2)
            context = "\n\n---\n\n".join(
                d.page_content[:800] for d in docs
            )

            llm = get_llm()
            prompt = f"""
You are a knowledgeable and helpful study assistant.

Use the provided context as the primary source of truth.
You may explain, simplify, or summarize the content.
Do not introduce new facts beyond the context. 
Provide a clear, structured, and detailed explanation when appropriate.
Use paragraphs and examples if helpful.

Context:
{context}

Question:
{user_query}

Answer:
"""
            response = llm.invoke(prompt)

        st.write(response)

    # Store assistant message
    messages.append({"role": "assistant", "content": response})

    # Persist updated chat to disk
    save_chats(chats)
