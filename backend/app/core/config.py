"""
Configuration settings for the AI Voice Agent API.
Uses Pydantic Settings for environment variable management.
"""

from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI Voice Agent API"
    DEBUG: bool = False

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Retell AI Configuration
    RETELL_API_KEY: str = ""
    RETELL_WEBHOOK_SECRET: str = ""

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Admin User Configuration
    ADMIN_EMAIL: str = "admin@localhost"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "System Administrator"

    # Logging Configuration
    LOG_TO_FILE: bool = True
    LOG_LEVEL: str = "INFO"

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 10

    # Retell API Configuration
    RETELL_API_TIMEOUT: int = 30
    RETELL_MAX_RETRIES: int = 3

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()