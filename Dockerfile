# Pinned to the exact Python version this project has been developed and
# tested against (see .python-version) — reproducibility between local dev
# and deployment, not an arbitrary choice.
FROM python:3.12.10-slim

# Without this, Python block-buffers stdout/stderr when it isn't attached
# to a terminal (true inside any container) — if the process crashes or is
# killed before the buffer fills, whatever it already printed (including a
# startup traceback) never reaches `docker logs` / the platform's log tab.
ENV PYTHONUNBUFFERED=1

# libmagic is required by `unstructured` (used for .pptx loading) for file
# type detection; nothing else in requirements.txt needs a system library
# beyond what the published wheels already bundle.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installed before copying the rest of the source so this layer is only
# rebuilt when dependencies actually change.
COPY requirements.txt .

# `sentence-transformers` pulls in `torch` transitively, and without this,
# pip's default Linux wheel for torch bundles the full CUDA runtime
# (several GB of NVIDIA libraries) even though this app only ever runs
# CPU-only inference. Installing the CPU-only build first (from PyTorch's
# own index) satisfies that dependency before requirements.txt gets to it,
# cutting both image size and build time dramatically — this is the
# difference between a build that takes a couple of minutes and one that
# can take 15-20+ minutes or hit a platform's build timeout.
RUN pip install --no-cache-dir torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user; give it a real $HOME so libraries that cache
# under it (e.g. the HuggingFace embedding model) have somewhere to write.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser
ENV HOME=/home/appuser

EXPOSE 8000

# $PORT is provided by the hosting platform at runtime; 8000 is only a local
# fallback. Shell form (not exec-array form) so the variable expands.
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
