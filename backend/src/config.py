from pydantic_settings import BaseSettings
from . import printmeup as pm

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    if not set
    """
    #* PostgreSQL (single database for everything)
    postgres_url: str = "postgresql://medicallm:medicallm@localhost:5432/drugbank"
    
    #* Auth
    jwt_secret: str = "supersecretkey"
    jwt_expiry_hours: int = 168
    
    #* LLM models (Digital Ocean AI)
    model_access_key: str = ""
    do_ai_model: str = "openai-gpt-oss-120b"

    #* Embedding model
    hgf_embedding_model_id: str = "nomic-ai/nomic-embed-text-v1"
    hf_token: str = ""  # HuggingFace API token (optional, for private models)
    
    #* PubMed / NCBI E-utilities
    pubmed_tool_name: str = "MedicaLLM"
    pubmed_email: str = "medicallm@example.com"
    pubmed_max_results: int = 10
    #* Optional NCBI API key — raises the rate limit from 3 to 10 req/s.
    #* Register at https://www.ncbi.nlm.nih.gov/account/
    ncbi_api_key: str = ""
    
    #* Scopus API (optional — for journal-level metrics)
    scopus_api_key: str = ""

    #* Cached document ttl
    document_cache_ttl_hours: int = 24
    pubmed_citation_ttl_seconds: int = 30 * 24 * 3600  # 30 days
    
    #* pdf storage
    pdf_dir: str = "data/pdf"
    downloaded_pdf_dir: str = "data/pdf/downloaded"
    pubmed_pdf_subdir: str = "data/pdf/pubmed"

    #* Admin panel
    admin_username: str = "medicallm"
    admin_password: str = "sezeristan000"

    #* Vector store
    vector_store_persist_dir: str = "chromadb-data"

    #* Logging
    log_level: str = "INFO"
    app_name: str = "MedicaLLM"
    
    class Config:
        env_file = ("../.env", ".env")

try:
    settings = Settings()
except Exception as e:
    pm.err(e)
    raise