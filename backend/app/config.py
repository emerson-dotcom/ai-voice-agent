from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Voice Agent API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - SUPABASE REQUIRED BY ASSIGNMENT
    DATABASE_URL: str  # Must be Supabase PostgreSQL connection string
    
    # Authentication
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for development
    ALGORITHM: str = "HS256"
    
    # Retell AI
    RETELL_API_KEY: str
    RETELL_BASE_URL: str = "https://api.retellai.com/v2"
    RETELL_WEBHOOK_SECRET: str
    RETELL_MOCK_MODE: bool = False  # Set to False to use real Retell API
    
    @field_validator('RETELL_MOCK_MODE')
    @classmethod
    def validate_mock_mode(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    RETELL_PHONE_NUMBER: str = "12262410232"  # Your actual Retell phone number (no + prefix)
    RETELL_DEFAULT_LLM_ID: Optional[str] = None  # Optional: specify a specific LLM ID to use
    RETELL_AUTO_CREATE_LLM: bool = True  # Automatically create LLM if none exists
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Supabase (Modern approach - primarily using direct PostgreSQL connection)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    # Note: We primarily use DATABASE_URL for direct PostgreSQL connection
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # WebSocket
    SOCKET_CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
