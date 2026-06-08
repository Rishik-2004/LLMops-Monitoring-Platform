"""
Core configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LLMOps Monitoring Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/llmops"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://llmops-platform.vercel.app",
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # LLM Providers
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Default LLM
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@llmops-platform.com"
    EMAILS_FROM_NAME: str = "LLMOps Platform"
    
    # Telemetry
    OTEL_EXPORTER_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "llmops-platform"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Langfuse (optional tracing)
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: Optional[str] = "https://cloud.langfuse.com"
    
    # Security Detection Thresholds
    INJECTION_THRESHOLD: float = 0.7
    TOXICITY_THRESHOLD: float = 0.6
    HALLUCINATION_THRESHOLD: float = 0.5
    
    # Alert Defaults
    DEFAULT_COST_ALERT_THRESHOLD: float = 10.0  # USD
    DEFAULT_LATENCY_ALERT_THRESHOLD: float = 5000.0  # ms
    DEFAULT_ERROR_RATE_ALERT_THRESHOLD: float = 0.1  # 10%
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
