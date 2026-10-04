import os
from pathlib import Path
from typing import List

from fastembed import TextEmbedding

# fastembed's own default cache dir is tempfile.gettempdir()/fastembed_cache
# — on most container platforms (including Render) /tmp is RAM-backed
# (tmpfs), so downloading and unpacking the ~90MB model there at runtime
# burns into the same memory budget as everything else, on top of the
# network fetch itself. Pointing it at a path baked into the Docker image
# instead (see Dockerfile's pre-fetch RUN step) means a cold start never
# downloads or writes anything at request time — it just reads files
# already on disk from the image layer.
_CACHE_DIR = Path(os.getenv("FASTEMBED_CACHE_PATH", Path(__file__).resolve().parent.parent / ".fastembed_cache"))

_model: TextEmbedding | None = None


class _FastEmbedAdapter:
    """Wraps fastembed's TextEmbedding to expose the embed_query/
    embed_documents interface the rest of the app expects (previously
    provided by langchain_huggingface.HuggingFaceEmbeddings)."""

    def __init__(self, model: TextEmbedding):
        self._model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Capped (fastembed's own default is 256) so one large document's
        # chunks don't all get tokenized/inferred as a single onnxruntime
        # batch at once — smaller batches bound the peak tensor memory of
        # any one `embed()` call, at the cost of a few more inference calls.
        return [vec.tolist() for vec in self._model.embed(texts, batch_size=32)]

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

    `threads=1` keeps onnxruntime from spinning up a thread pool sized to
    the host's CPU count (each intra/inter-op thread gets its own working
    buffers — wasted overhead on a 0.1 CPU free-tier instance anyway).
    `enable_cpu_mem_arena=False` turns off onnxruntime's CPU memory arena,
    which by default grows to the largest allocation it's ever seen and
    never shrinks for the life of the process; without it, every allocation
    is freed back to the OS as soon as it's no longer needed, so memory
    doesn't ratchet upward across repeated uploads in the same process.
    """
    global _model
    if _model is None:
        _model = TextEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_dir=str(_CACHE_DIR),
            threads=1,
            enable_cpu_mem_arena=False,
        )
    return _FastEmbedAdapter(_model)
