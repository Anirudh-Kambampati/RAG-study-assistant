import json
from pathlib import Path

STORE = Path("chat_store.json")

def load_chats():
    if not STORE.exists():
        return {}
    return json.loads(STORE.read_text())

def save_chats(chats):
    STORE.write_text(json.dumps(chats, indent=2))
