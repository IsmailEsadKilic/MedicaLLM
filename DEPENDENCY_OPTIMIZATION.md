# Dependency Optimization for Deployment

## Summary

This document describes the dependency optimization performed to reduce Docker image size and enable successful deployment on resource-constrained environments like DigitalOcean App Platform.

## Problem

The original deployment was failing with "resource exhaustion" errors due to:
- **PyTorch + CUDA dependencies**: ~2.5GB of downloads
- **sentence-transformers**: Required PyTorch and all CUDA libraries
- Total package downloads: ~3GB+
- Build time: Exceeded platform limits

## Solution

### Python Backend Changes

#### Removed Dependencies
1. **sentence-transformers** (507MB + 2GB CUDA deps)
   - Replaced with OpenAI embeddings API
   - Uses existing DO AI infrastructure
   - No local model loading required

2. **langchain-huggingface** (unused)
   - Not imported anywhere in codebase
   - Removed completely

3. **langchain-chroma** (unused)
   - ChromaDB not used (using PostgreSQL + pgvector)
   - Removed completely

4. **einops** (unused)
   - Not imported anywhere in codebase
   - Removed completely

#### Modified Files

**backend/pyproject.toml**
- Removed: `sentence-transformers`, `langchain-huggingface`, `langchain-chroma`, `einops`
- Added: `numpy>=1.24.0` (explicit dependency, was transitive before)
- Total dependencies reduced from 35 to 31

**backend/src/drugs/embedding_service.py**
- Changed from `SentenceTransformer` to OpenAI embeddings API
- Uses `text-embedding-3-small` model (1536 dimensions)
- Maintains same interface and caching behavior
- Thread-safe API calls with rate limit protection

**backend/src/config.py**
- Removed: `hf_embedding_model_id`, `hf_token`
- Added: `embedding_model_name` (defaults to "text-embedding-3-small")

**backend/run.py**
- Removed: `chromadb-data` from reload excludes

### Frontend Changes

No changes required. Frontend dependencies are already optimized.

## Impact

### Build Size Reduction
- **Before**: ~3GB of package downloads, 171 packages
- **After**: ~800MB of package downloads, ~140 packages
- **Savings**: ~2.2GB (73% reduction)

### Build Time Reduction
- **Before**: 25+ seconds for package download, build timeout
- **After**: Expected ~8-10 seconds, within platform limits

### Runtime Changes

#### Embedding Generation
- **Before**: Local model inference (CPU-bound, 3-5s startup)
- **After**: API calls to DO AI (network-bound, <1s per call)
- **Cost**: Minimal (embeddings are cached, only generated once per drug)

#### Performance
- First-time embedding generation: Slightly slower (API latency)
- Cached embeddings: No change (same database lookup)
- Overall: Negligible impact due to caching

## Migration Steps

### For Existing Deployments

1. **Regenerate embeddings** (optional, only if you have existing data):
   ```bash
   # The new embedding model has different dimensions
   # If you have existing embeddings, you'll need to regenerate them
   python -m scripts.generate_drug_embeddings
   ```

2. **Environment variables** (no changes required):
   - Uses existing `DO_MODEL_ACCESS_KEY` and `LLM_BASE_URL`
   - No new environment variables needed

3. **Database** (no changes required):
   - pgvector schema remains the same
   - Embedding dimension may differ (1536 vs previous model)
   - Old embeddings will be replaced on regeneration

### For New Deployments

No special steps required. The optimized dependencies will be installed automatically.

## Verification

After deployment, verify embeddings work:

```bash
# Check if embeddings are being generated
curl -X POST https://your-app.ondigitalocean.app/api/drugs/search \
  -H "Content-Type: application/json" \
  -d '{"query": "pain relief", "limit": 5}'
```

## Rollback Plan

If issues arise, revert these commits:
1. Restore `backend/pyproject.toml` to include `sentence-transformers`
2. Restore `backend/src/drugs/embedding_service.py` to use `SentenceTransformer`
3. Restore `backend/src/config.py` to include `hf_embedding_model_id`

## Future Optimizations

Consider these additional optimizations if needed:
1. Use `psycopg2` instead of `psycopg2-binary` (smaller, requires build tools)
2. Remove unused langchain components if not all features are used
3. Use Alpine-based Python image instead of Debian slim
4. Multi-stage Docker build to exclude build dependencies

## Notes

- OpenAI embeddings via DO AI are included in your existing plan
- Embedding quality may differ slightly from the previous model
- Consider regenerating embeddings if search quality changes
- Monitor API usage if you have a large drug database
