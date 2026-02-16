# Use Python 3.11 slim image
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency files
COPY pyproject.toml ./

# Option A: If using local embeddings (sentence-transformers)
# Install PyTorch CPU-only first to avoid CUDA bloat
RUN uv pip install --system --no-cache \
    torch --index-url https://download.pytorch.org/whl/cpu

# Option B: If using Bedrock Titan embeddings (recommended)
# Remove the torch installation above entirely

# Install remaining dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code (excluding data, chromadb-data, .venv via .dockerignore)
COPY . .

# Create necessary directories (will be mounted as volumes)
RUN mkdir -p chromadb-data data/pdf data/xml/drugbank

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]