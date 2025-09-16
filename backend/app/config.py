from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Voice Agent API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - SUPABASE REQUIRED BY ASSIGNMENT
    DATABASE_URL: str  # Must be Supabase PostgreSQL connection string
    
    # Authentication
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Retell AI
    RETELL_API_KEY: str
    RETELL_BASE_URL: str = "https://api.retellai.com/v2"
    RETELL_WEBHOOK_SECRET: str
    
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
