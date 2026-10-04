from typing import List

from fastembed import TextEmbedding

_model: TextEmbedding | None = None


class _FastEmbedAdapter:
    """Wraps fastembed's TextEmbedding to expose the embed_query/
    embed_documents interface the rest of the app expects (previously
    provided by langchain_huggingface.HuggingFaceEmbeddings)."""

    def __init__(self, model: TextEmbedding):
        self._model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> List[float]:
        return next(iter(self._model.query_embed([text]))).tolist()


def get_embedding_model() -> _FastEmbedAdapter:
    """Same model, weights, and output dimension as before
    (sentence-transformers/all-MiniLM-L6-v2) — only the runtime changes,
    from PyTorch to ONNX via fastembed. PyTorch's CPU runtime overhead alone
    (hundreds of MB, before even counting the model) was enough, stacked on
    top of the rest of this app, to exceed a 512MB host's memory limit;
    onnxruntime's footprint for the same model is a fraction of that.

    Cached as a module-level singleton — the previous version constructed a
    fresh model instance on every call, reloading weights into memory each
    time instead of reusing one.
    """
    global _model
    if _model is None:
        _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _FastEmbedAdapter(_model)
