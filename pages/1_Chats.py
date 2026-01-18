import streamlit as st
from chat_utils import load_chats


st.set_page_config(page_title="Chats", layout="wide")
st.title("💬 Your Chats")

# Load chats from disk
chats = load_chats()

if not chats:
    st.info("No chats available. Create one from the New Chat page.")
    st.stop()

st.subheader("Select a chat to continue")

for doc_id in chats.keys():
    if st.button(doc_id):
        st.session_state.active_doc = doc_id
        st.switch_page("pages/2_Chat.py")
