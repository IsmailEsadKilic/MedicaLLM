from pydantic_settings import BaseSettings
from . import printmeup as pm

class Settings(BaseSettings):
    # LLM models
    bedrock_llm_id: str = "anthropic.claude-3-haiku-20240307-v1:0"  # alias for bedrock_model_id
    hgf_llm_id: str = "google/gemma-3-1b-it"

    # Embedding model
    embedding_model_id: str = "nomic-ai/nomic-embed-text-v1"
    
    # AWS config
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "dummy"
    aws_secret_access_key: str = "dummy"
    dynamodb_endpoint: str = "http://localhost:8001"  # Use localhost:8001 for local dev, override via env for Docker
    
    # Auth
    jwt_secret: str = "supersecretkey"
    jwt_expiry_hours: int = 168
    
    # Logging
    log_level: str = "INFO"
    app_name: str = "MedicaLLM"
    
    class Config:
        env_file = ("../.env", ".env")

try:
    settings = Settings()
except Exception as e:
    pm.err(e)
    raise