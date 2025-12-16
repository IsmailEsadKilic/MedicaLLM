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

# Install PyTorch CPU-only first (to avoid CUDA dependencies)
RUN uv pip install --system --no-cache \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies using UV
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code (excluding data, chroma_db, .venv via .dockerignore)
COPY . .

# Copy scripts directory
COPY scripts /scripts

# Create necessary directories (will be mounted via volumes)
RUN mkdir -p chroma_db data/pdf data/xml/drugbank

# Setup entrypoint script - fix line endings and make executable
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 2580

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:2580/health')" || exit 1

# Run the application via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
