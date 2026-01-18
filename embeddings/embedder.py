from langchain_ollama import OllamaEmbeddings


def get_embedding_model():
    return OllamaEmbeddings(model="nomic-embed-text")