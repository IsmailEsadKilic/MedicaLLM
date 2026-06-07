import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict

from logging import getLogger

logger = getLogger(__name__)


# Empty sentinel — empty string means "no default; must be provided via env"
_REQUIRED = ""


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    if not set, default values will be used.
    """
    # Auth
    # JWT secret MUST be provided via env in any non-dev deployment. We generate
    # a per-process random fallback so dev still works, but tokens won't be
    # valid across restarts unless the env var is set (S2).
    jwt_secret: str = ""
    jwt_expiry_hours: int = 168
    
    # LLM models (Digital Ocean AI)
    # Both env-var aliases supported for backwards compatibility:
    #   DO_MODEL_ACCESS_KEY (legacy / .env.example) and MODEL_ACCESS_KEY (compose.yml)
    do_model_access_key: str = ""
    do_llm_model_id: str = "openai-gpt-oss-120b"
    
    # Scopus API (optional — for citation metrics)
    scopus_api_key: str | None = None
    scopus_use_for_citations: bool = True  # Use Scopus instead of Semantic Scholar when available

    # OpenAlex (free, used for FWCI when Scopus Abstract Retrieval is not accessible)
    openalex_enabled: bool = True
    openalex_email: str | None = None  # Optional, used for OpenAlex "polite pool"

    # Europe PMC full text (free; fetches Methods/Results/Discussion for open-access articles)
    fulltext_enabled: bool = True
    # Max articles to fetch full text for. 0 = no limit (fetch for all search results).
    # Set to a positive integer to bound latency when needed.
    fulltext_max_articles: int = 0
    # Per-section char cap — balances depth vs. LLM context budget.
    # Most clinically useful sections (methods/results/conclusion) rarely exceed 8k chars.
    fulltext_max_chars_per_section: int = 8000

    # Embedding model
    hf_embedding_model_id: str = "nomic-ai/nomic-embed-text-v1"
    hf_token: str = ""  # HuggingFace API token (optional, for private models)

    # Logging — INFO is the right default for production. DEBUG is opt-in via env.
    log_dir: str = "logs"
    log_level: str = "INFO"
    app_name: str = "MedicaLLM"
    
    # Admin panel
    # Admin password MUST be provided via env (no hardcoded default) — see S1.
    admin_username: str = "medicallm"
    admin_password: str = ""
    
    # Database
    # Postgres URL must come from env. Aliased so both env-var conventions work
    # (DO_POSTGRES_URL and POSTGRES_URL — see I3).
    do_postgres_url: str = ""
    
    api_version: str = "1.0.0"
    
    # CORS — comma-separated list of allowed frontend origins. Defaults are dev-only.
    cors_allowed_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:4000,http://localhost:5173"
    )
    
    # Cached document ttl
    document_cache_ttl_hours: int = 24
    pubmed_citation_ttl_seconds: int = 30 * 24 * 3600  # 30 days
    pubmed_search_cache_ttl_seconds: int = 7 * 24 * 3600  # 7 days
    
    # PubMed / NCBI E-utilities
    pubmed_tool_name: str = "MedicaLLM"
    pubmed_email: str = "medicallm@example.com"
    # Default articles to retrieve when the agent doesn't override (used by tools)
    pubmed_max_results: int = 10
    # Lower bound below which we drop low-quality matches
    pubmed_min_confidence: float = 35.0
    ncbi_api_key: str | None = None
    
    # score weights
    boost_impact_score_weights: bool = False
    
    # pdf storage
    pdf_dir: str = "data/pdf"
    
    # Rate limits (for external API calls)
    llm_limit: str = "10/minute"
    search_limit: str = "60/minute"
    auth_limit: str = "20/minute"

    # Daily message quota (free tier). Premium users (UserRecord.is_premium)
    # bypass this completely. Counted on successful query / query-stream
    # invocations only — failed requests do not consume the quota.
    free_daily_message_quota: int = 20

    # Registration abuse controls
    # Max account-creations per IP per UTC day. Set to 0 to disable.
    registration_daily_ip_cap: int = 5

    # Email delivery
    # ───────────────
    # Provider selector: "resend" (HTTPS API, recommended on cloud hosts that
    # block outbound SMTP), "smtp" (Hostinger / generic SMTP), or "auto"
    # which prefers Resend when RESEND_API_KEY is set and falls back to SMTP.
    email_provider: str = "auto"

    # Resend (HTTPS API — bypasses DigitalOcean's outbound SMTP block).
    # Get a key at https://resend.com/api-keys with `Sending access` only.
    resend_api_key: str = ""
    # `Display Name <addr>` form. Domain must be verified in Resend first.
    resend_from_address: str = "MedicaLLM <noreply@medicallm.com.tr>"
    resend_reply_to: str = ""

    # SMTP — leave host empty to fall back to log-only delivery (dev mode).
    # Hostinger settings:
    #   smtp_host=smtp.hostinger.com  smtp_port=465  smtp_use_ssl=true
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_ssl: bool = True
    smtp_use_starttls: bool = False
    # Friendly-name + address used in the From: header. Defaults to the
    # username when only smtp_username is set.
    smtp_from_address: str = ""
    smtp_from_name: str = "MedicaLLM"
    # Where the user is sent for password resets / verification follow-ups.
    # Used inside the email template's CTA button.
    public_app_url: str = "https://medicallm.com.tr"
    
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
    
    # Pydantic v2: SettingsConfigDict replaces inner `class Config`. The legacy
    # `class Config` did not always pick up env vars correctly under v2.
    # `populate_by_name=True` lets us map several env-var aliases to a single field.
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Env-var aliases — accept both legacy and compose.yml conventions so
        # the app loads regardless of which form is set in the environment.
        # See AUDIT_REPORT items I2 (MODEL_ACCESS_KEY vs DO_MODEL_ACCESS_KEY)
        # and I3 (POSTGRES_URL vs DO_POSTGRES_URL).
        if not self.do_model_access_key:
            self.do_model_access_key = os.getenv("MODEL_ACCESS_KEY", "")
        if not self.do_postgres_url:
            self.do_postgres_url = os.getenv("POSTGRES_URL", "")
        # DO_AI_MODEL is the env-var name used by compose.yml.
        env_model = os.getenv("DO_AI_MODEL")
        if env_model:
            self.do_llm_model_id = env_model

        # Mirror the Hugging Face token into the process environment so
        # downstream libraries that read HF_TOKEN/HUGGINGFACE_HUB_TOKEN
        # directly can authenticate during model download.
        if self.hf_token:
            os.environ.setdefault("HF_TOKEN", self.hf_token)
            os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", self.hf_token)

        # JWT secret: warn if missing, generate a random per-process fallback so
        # dev still works without an env var. NEVER fall back to a known string.
        if not self.jwt_secret:
            self.jwt_secret = secrets.token_urlsafe(48)
            logger.warning(
                "JWT_SECRET not set — generated an ephemeral random secret for "
                "this process. Tokens will be invalidated on restart and will "
                "not work across multiple workers. Set JWT_SECRET in production."
            )
        elif self.jwt_secret in ("supersecretkey", "change-me-in-production", "change-me"):
            logger.error(
                "JWT_SECRET is set to a known weak placeholder value. "
                "Generate a strong random secret (e.g., `openssl rand -base64 48`) "
                "and set it via the JWT_SECRET env var."
            )

        if not self.admin_password:
            logger.warning(
                "ADMIN_PASSWORD not set — admin login is disabled. "
                "Set ADMIN_PASSWORD in the environment to enable the admin panel."
            )


try:
    settings = Settings()
except Exception as e:
    logger.error(f"Error loading settings: {str(e)}")
    raise
