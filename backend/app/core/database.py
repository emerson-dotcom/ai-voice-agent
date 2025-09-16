from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import asyncio


# Create async engine - SUPABASE POSTGRESQL REQUIRED BY ASSIGNMENT
DATABASE_URL = getattr(settings, 'DATABASE_URL', None)

# Validate that Supabase is configured (assignment requirement)
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is required! Please set your Supabase database URL in .env file")

if not DATABASE_URL.startswith('postgresql'):
    raise ValueError("❌ Assignment requires Supabase PostgreSQL! Please use a valid Supabase DATABASE_URL")

if 'YOUR_PROJECT_REF' in DATABASE_URL or 'YOUR_PASSWORD' in DATABASE_URL:
    raise ValueError("❌ Please update your .env file with actual Supabase credentials (replace YOUR_PROJECT_REF and YOUR_PASSWORD)")

print(f"✅ Connecting to Supabase PostgreSQL: {DATABASE_URL.split('@')[0]}...")

# Auto-fix for pgbouncer: Use correct pooler URL with proper user format
final_url = DATABASE_URL

# Auto-convert to working Supabase pooler configuration
if 'epczdshrbckigsdfqush' in DATABASE_URL:
    # Extract password from the original URL
    import re
    password_match = re.search(r'://[^:]+:([^@]+)@', DATABASE_URL)
    password = password_match.group(1) if password_match else 'PASSWORD_NOT_FOUND'
    
    # Use the correct pooler configuration from user
    final_url = f"postgresql+asyncpg://postgres.epczdshrbckigsdfqush:{password}@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
    
    print("🔄 Using correct Supabase pooler configuration")
    print(f"🔗 Host: aws-1-ap-southeast-1.pooler.supabase.com:5432")
    print(f"👤 User: postgres.epczdshrbckigsdfqush")
    print(f"🏊 Pool Mode: session")

engine = create_async_engine(
    final_url,
    echo=getattr(settings, 'DEBUG', True),
    future=True,
    pool_pre_ping=True,  # Supabase connection health check
    pool_recycle=3600,   # Refresh connections hourly for Supabase
    connect_args={
        "statement_cache_size": 0,  # Disable prepared statements for pgbouncer
        "prepared_statement_cache_size": 0,  # Alternative parameter name
        "server_settings": {
            "application_name": "ai-voice-agent",
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import agent, call, user
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
