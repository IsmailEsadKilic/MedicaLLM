"""
Runner for MedicaLLM backend.

Run this with: uv run run.py OR python run.py
OR the application can be run with: uvicorn src.main:app --host 0.0.0.0 --port 8000

this file is just a wrapper around uvicorn to allow for easier local development and debugging.
Because of `reload=True`, the server will automatically restart when code changes are detected,
which is ideal for development.
not intended for production use.
in production, the application should be run with uvicorn directly
without `reload=True` for better performance and stability.
"""
from pathlib import Path

from dotenv import load_dotenv
import uvicorn

_BASE_DIR = Path(__file__).resolve().parent

# Load environment variables before Uvicorn imports the app so reload workers
# inherit the Hugging Face token and any other local settings.
load_dotenv(_BASE_DIR / ".env")
load_dotenv(_BASE_DIR.parent / ".env", override=False)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv", "*.pyc", "__pycache__", "chromadb-data", "data", "logs"],
    )
