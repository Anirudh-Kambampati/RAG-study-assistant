import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from vector_store.faiss_store import load_faiss_index
from llm.generator import get_llm
from chat_utils import load_chats, save_chats


st.set_page_config(page_title="Chat", layout="wide")

# Safety check
if "active_doc" not in st.session_state:
    st.error("No chat selected. Go to the Chats page.")
    st.stop()

doc_id = st.session_state.active_doc

# Load chats
chats = load_chats()

if doc_id not in chats:
    st.error("Chat not found.")
    st.stop()

messages = chats[doc_id]["messages"]

# Load vector store
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
    # Save user message
    messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            k=4
            docs = vectorstore.similarity_search(user_query, k=k)

            context = "\n\n---\n\n".join(
                d.page_content[:1200] for d in docs
            )

            llm = get_llm()

            prompt = f"""
You are a knowledgeable and friendly academic assistant.

Guidelines:
- Answer clearly and confidently.
- Use ONLY the information in the context. you MAY use your knowledge base to simplify and explain the context.
- Do not invent or assume anything.
- If the answer is not in the context, tell the user that the document does not contain the answer.
- If answer is incomplete, Use general knowledge to complete the answer, in that case, clearly indicate which parts are based on:
   - "From the document"
   - "From general knowledge".
Style:
- Calm, clear, and slightly conversational
- Well-structured explanations
- Helpful, but not overly verbose

Formatting & presentation rules:
- Use clear Markdown formatting.
- Use headings (##, ###) to organize sections logically.
- Use bullet points for lists and key takeaways.
- Use tables when comparing concepts, differences, or components.
- Use code blocks when showing:
  - workflows
  - pipelines 
  - step-by-step flows
  - pseudo-code or structured logic
  - code snippets
- Do NOT use code blocks for normal text explanations.
- Keep formatting clean and readable and decorative.

Format:
- Clear explanation with paraphrases
- Key points (bullets)
- Simplified Explanation
- Summary

Context:
{context}

Question:
{user_query}

Answer:
"""
            try:
                response = llm.invoke(prompt)
            except Exception as e:
                print(f"⚠️ Primary LLM failed: {e}")
                from llm.generator import get_fallback_llm
                fallback_llm = get_fallback_llm()
                
                response = fallback_llm.invoke(prompt)

            # ✅ FIX: extract TEXT ONLY
            assistant_text = (
                response.content
                if hasattr(response, "content")
                else str(response)
            )

        st.write(assistant_text)

    # Save assistant message (TEXT ONLY)
    messages.append(
        {"role": "assistant", "content": assistant_text}
    )

    save_chats(chats)
