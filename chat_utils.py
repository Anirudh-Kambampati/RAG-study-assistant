import json
from pathlib import Path

CHAT_STORE = Path("chat_store.json")


def load_chats() -> dict:
    if not CHAT_STORE.exists():
        return {}
    with open(CHAT_STORE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chats(chats: dict) -> None:
    with open(CHAT_STORE, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2)
