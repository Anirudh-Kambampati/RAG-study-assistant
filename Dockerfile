# Pinned to the exact Python version this project has been developed and
# tested against (see .python-version) — reproducibility between local dev
# and deployment, not an arbitrary choice.
FROM python:3.12.10-slim

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
