FROM python:3.13-slim

# Install `uv` (Astral's fast Python package manager).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_DIR=logs

# Create the non-root user up-front so the later `--chown=appuser:appuser`
# COPY and `USER appuser` directives have a real account to point at.
# Audit I1: the previous Dockerfile referenced `appuser` but never created
# it, so the build failed at the `USER appuser` step.
RUN groupadd --system --gid 1001 appuser \
 && useradd --system --uid 1001 --gid appuser --home /app --shell /usr/sbin/nologin appuser

# Copy dependency files and install dependencies as root (so /usr/local site
# packages are writable). We pin to the lockfile-style behaviour by using
# `--no-cache` and re-resolving against pyproject.toml on every build.
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the rest of the application, owned by the non-root user.
COPY --chown=appuser:appuser . .

# Pre-create the runtime directories with appuser ownership BEFORE the volume
# mounts happen. When Docker initializes an empty named volume on top of one
# of these paths, it inherits the underlying directory's ownership — without
# this, the volumes come up root-owned and the non-root appuser can't write.
RUN mkdir -p /app/logs /app/data/pdf/pubmed /app/data/pdf/pubmed_downloads /app/chromadb-data \
 && chown -R appuser:appuser /app/logs /app/data /app/chromadb-data

USER appuser

EXPOSE 8000

# Real health check — the in-app /health endpoint pings the DB and the agent.
# Returning 503 here makes Docker's healthcheck flip to "unhealthy", which
# also unblocks `depends_on: condition: service_healthy` in compose.yml.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; r=urllib.request.urlopen('http://localhost:8000/health',timeout=5); sys.exit(0 if r.status==200 else 1)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
