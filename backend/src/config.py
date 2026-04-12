from pydantic_settings import BaseSettings
from . import printmeup as pm


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    if not set
    """

    # * AWS config
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "dummy"
    aws_secret_access_key: str = "dummy"

    # * DynamoDB config for local development with DynamoDB Local
    # * this value will be overridden in docker-compose
    # * to point to the internal network address of the DynamoDB container
    dynamodb_endpoint: str = "http://localhost:8001"

    # * Auth
    jwt_secret: str = "supersecretkey"
    jwt_expiry_hours: int = 168

    # * LLM models
    bedrock_llm_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    hgf_llm_id: str = "google/gemma-3-1b-it"

    # * Embedding model
    hgf_embedding_model_id: str = "nomic-ai/nomic-embed-text-v1"

    # * PubMed / NCBI E-utilities
    pubmed_tool_name: str = "MedicaLLM"
    pubmed_email: str = "medicallm@example.com"
    pubmed_max_results: int = 3
    # * Optional NCBI API key — raises the rate limit from 3 to 10 req/s.
    # * Register at https://www.ncbi.nlm.nih.gov/account/
    ncbi_api_key: str = ""

    # * Cached document ttl
    document_cache_ttl_hours: int = 24

    # * pdf storage
    pdf_dir: str = "data/pdf"
    downloaded_pdf_dir: str = "data/pdf/downloaded"

    # * Vector store
    vector_store_persist_dir: str = "chromadb-data"

    # * Logging
    log_level: str = "INFO"
    app_name: str = "MedicaLLM"

    class Config:
        env_file = ("../.env", ".env")


try:
    settings = Settings()
except Exception as e:
    pm.err(e)
    raise
