from pydantic_settings import BaseSettings
from . import printmeup as pm

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    if not set, default values will be used.
    """
    # Auth
    jwt_secret: str = "supersecretkey"
    jwt_expiry_hours: int = 168
    
    # LLM models (Digital Ocean AI)
    do_model_access_key: str = ""
    do_llm_model_id: str = "openai-gpt-oss-120b"
    
    # Scopus API (optional — for journal-level metrics)
    scopus_api_key: str | None = None

    # Embedding model
    hgf_embedding_model_id: str = "nomic-ai/nomic-embed-text-v1"
    hf_token: str = ""  # HuggingFace API token (optional, for private models)

    # Logging
    log_level: str = "INFO"
    app_name: str = "MedicaLLM"
    
    # Admin panel
    admin_username: str = "medicallm"
    admin_password: str = "sezeristan000"
    
    # Database
    do_postgres_url: str = "postgresql://medicallm:medicallm@localhost:5432/drugbank"
    
    #section
    
    api_version: str = "1.0.0"
    
    # Cached document ttl
    document_cache_ttl_hours: int = 24
    pubmed_citation_ttl_seconds: int = 30 * 24 * 3600  # 30 days
    pubmed_search_cache_ttl_seconds: int = 7 * 24 * 3600  # 7 days
    
    # PubMed / NCBI E-utilities
    pubmed_tool_name: str = "MedicaLLM"
    pubmed_email: str = "medicallm@example.com"
    pubmed_max_results: int = 15
    ncbi_api_key: str | None = None
    
    # pdf storage
    pdf_dir: str = "data/pdf"
    
    llm_limit: str = "10/minute"
    search_limit: str = "60/minute"
    auth_limit: str = "20/minute"
    
    # LLM Configuration
    llm_model_id = do_llm_model_id
    llm_api_key = do_model_access_key
    llm_base_url = "https://inference.do-ai.run/v1"
    llm_max_tokens = 4096
    llm_temperature = 0.0
    llm_max_iterations = 50
    llm_streaming = True
    
    # Conversation Session
    max_n_sessions: int = 100
    session_ttl_seconds: int = 1800  # 30 minutes
    
    class Config:
        env_file = ("../.env", ".env")

try:
    settings = Settings()
except Exception as e:
    pm.err(e)
    raise