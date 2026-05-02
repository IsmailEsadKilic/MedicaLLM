from pydantic_settings import BaseSettings

from logging import getLogger

logger = getLogger(__name__)

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
    log_dir: str = "logs"
    log_level: str = "DEBUG"  # Changed from INFO to DEBUG for comprehensive logging
    app_name: str = "MedicaLLM"
    
    # Admin panel
    admin_username: str = "medicallm"
    admin_password: str = "sezeristan000"
    
    # Database
    do_postgres_url: str = "" # no default
    
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
    
    # Rate limits (for external API calls)
    llm_limit: str = "10/minute"
    search_limit: str = "60/minute"
    auth_limit: str = "20/minute"
    
    # LLM Configuration
    @property
    def llm_model_id(self) -> str:
        return self.do_llm_model_id
        
    @property
    def llm_api_key(self) -> str:
        return self.do_model_access_key
        
    llm_base_url: str = "https://inference.do-ai.run/v1"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.0
    llm_max_iterations: int = 50
    llm_streaming: bool = True
    
    # database
    @property
    def postgres_url(self) -> str:
        return self.do_postgres_url
    
    # Conversation Session
    max_n_sessions: int = 100
    session_ttl_seconds: int = 1800  # 30 minutes
    default_conversation_title: str = "New Conversation"
    max_history_turns: int = 20  # ~40 messages (user + assistant each)
    
    # Agent
    default_agent_response: str = "I'm sorry, I couldn't generate a response."
    
    class Config:
        env_file = ("../.env", ".env")

try:
    settings = Settings()
except Exception as e:
    logger.error(f"Error loading settings: {str(e)}")
    raise