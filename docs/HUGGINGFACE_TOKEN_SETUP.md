# HuggingFace Token Setup Guide

## Overview

The HuggingFace token is used to authenticate with HuggingFace's model hub when downloading embedding models. It's **optional** for most public models but **required** for:
- Private models
- Gated models (models that require acceptance of terms)
- Rate-limited models
- Enterprise features

## When Do You Need It?

### ✅ You DON'T need it for:
- `nomic-ai/nomic-embed-text-v1` (public model) ✅ **Your current model**
- `sentence-transformers/all-MiniLM-L6-v2` (public model)
- Most open-source embedding models

### ⚠️ You NEED it for:
- Private models in your HuggingFace account
- Gated models (e.g., some Meta Llama models)
- Models that require terms acceptance
- If you hit rate limits on public models

## Setup Instructions

### Step 1: Get Your HuggingFace Token

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Log in or create an account
3. Click **"New token"**
4. Choose token type:
   - **Read**: For downloading models (recommended)
   - **Write**: For uploading models (not needed for MedicaLLM)
5. Copy the token (starts with `hf_...`)

### Step 2: Add Token to .env File

Open your `.env` file and add the token:

```bash
# HuggingFace token (optional, only needed for private/gated models)
HF_TOKEN=hf_YourTokenHere
```

**Example**:
```bash
HF_TOKEN=hf_abcdefghijklmnopqrstuvwxyz1234567890
```

### Step 3: Restart the Backend

```bash
cd backend
python run.py
```

The token will be automatically loaded and used when initializing embeddings.

## How It Works

### Code Flow

1. **Config Loading** (`backend/src/config.py`):
```python
class Settings(BaseSettings):
    hf_token: str = ""  # Loaded from HF_TOKEN env var
```

2. **Vector Store Initialization** (`backend/src/rag/vector_store.py`):
```python
model_kwargs = {"trust_remote_code": True}

# If HF_TOKEN is set, pass it to the embeddings
if settings.hf_token:
    model_kwargs["token"] = settings.hf_token

self.embeddings = HuggingFaceEmbeddings(
    model_name=hgf_embedding_model_id,
    model_kwargs=model_kwargs,
)
```

3. **HuggingFace Library**: Uses the token to authenticate API requests

## Alternative: Environment Variable

Instead of `.env`, you can set it as a system environment variable:

### Linux/Mac:
```bash
export HF_TOKEN=hf_YourTokenHere
```

### Windows (PowerShell):
```powershell
$env:HF_TOKEN="hf_YourTokenHere"
```

### Windows (CMD):
```cmd
set HF_TOKEN=hf_YourTokenHere
```

### Docker:
```yaml
# compose.yml
services:
  backend:
    environment:
      - HF_TOKEN=${HF_TOKEN}
```

Then run:
```bash
export HF_TOKEN=hf_YourTokenHere
docker-compose up
```

## Verification

### Check if Token is Loaded

Look for this log message when starting the backend:

```
[DEBUG] Using HuggingFace token for embeddings
```

If you don't see this message, the token is either:
- Not set in `.env`
- Empty string
- Not loaded (check `.env` file location)

### Test Embeddings

```python
# backend/test_embeddings.py
from src.config import settings
from langchain_huggingface import HuggingFaceEmbeddings

print(f"HF Token set: {bool(settings.hf_token)}")

model_kwargs = {"trust_remote_code": True}
if settings.hf_token:
    model_kwargs["token"] = settings.hf_token

embeddings = HuggingFaceEmbeddings(
    model_name=settings.hgf_embedding_model_id,
    model_kwargs=model_kwargs,
)

# Test embedding
result = embeddings.embed_query("Hello world")
print(f"✅ Embeddings working! Dimension: {len(result)}")
```

Run:
```bash
cd backend
python test_embeddings.py
```

## Security Best Practices

### ✅ DO:
- Keep your token in `.env` (not committed to git)
- Use **Read** tokens (not Write)
- Rotate tokens periodically
- Use different tokens for dev/prod

### ❌ DON'T:
- Commit `.env` to git (it's in `.gitignore`)
- Share your token publicly
- Use Write tokens unless needed
- Hardcode tokens in source code

## Troubleshooting

### Issue: "401 Unauthorized" when downloading model

**Cause**: Token not set or invalid

**Fix**:
1. Verify token in `.env`: `HF_TOKEN=hf_...`
2. Check token is valid on HuggingFace
3. Restart backend

### Issue: "Model not found" for gated model

**Cause**: Haven't accepted model terms

**Fix**:
1. Go to model page on HuggingFace
2. Accept terms/conditions
3. Wait for approval (usually instant)
4. Retry with token

### Issue: Token not loading

**Cause**: `.env` file not in correct location

**Fix**:
```bash
# Check .env location
ls -la .env          # Should be in project root
ls -la backend/.env  # Or in backend folder

# Verify Config class looks for it
# backend/src/config.py
class Config:
    env_file = ("../.env", ".env")  # Checks both locations
```

### Issue: Rate limiting even with token

**Cause**: Free tier rate limits

**Fix**:
- Upgrade to HuggingFace Pro
- Cache embeddings locally
- Use a different model

## Current Setup

For your current model (`nomic-ai/nomic-embed-text-v1`):
- ✅ **Token is OPTIONAL** (public model)
- ✅ **Works without token**
- ✅ **Token provides higher rate limits** (if needed)

## When to Add Token

Add the token if you experience:
- Rate limiting errors
- 401/403 authentication errors
- Slow model downloads
- Need to use private/gated models

## Summary

✅ **Optional for public models** (like your current one)
✅ **Easy to add**: Just set `HF_TOKEN` in `.env`
✅ **Secure**: Token stays in `.env` (not committed)
✅ **Automatic**: Code checks and uses token if present
✅ **No code changes needed**: Just environment variable

## Resources

- [HuggingFace Tokens Documentation](https://huggingface.co/docs/hub/security-tokens)
- [Get Your Token](https://huggingface.co/settings/tokens)
- [Model Hub](https://huggingface.co/models)
- [Rate Limits](https://huggingface.co/docs/hub/rate-limits)
