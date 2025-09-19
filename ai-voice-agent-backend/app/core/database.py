from supabase import create_client, Client
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    global supabase
    if supabase is None:
        try:
            supabase = create_client(settings.supabase_url, settings.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    return supabase


def test_connection() -> bool:
    """Test the database connection."""
    try:
        client = get_supabase_client()
        # Try to fetch from a simple table to test connection
        result = client.table("users").select("id").limit(1).execute()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def test_table_access() -> dict:
    """Test access to all required tables."""
    results = {}
    client = get_supabase_client()
    
    tables = ["users", "agents", "calls", "call_results"]
    
    for table in tables:
        try:
            result = client.table(table).select("id").limit(1).execute()
            results[table] = {"accessible": True, "count": len(result.data)}
            logger.info(f"Table {table} accessible")
        except Exception as e:
            results[table] = {"accessible": False, "error": str(e)}
            logger.error(f"Table {table} not accessible: {e}")
    
    return results


def create_user(email: str, role: str = "user") -> Optional[dict]:
    """Create a new user in the database."""
    try:
        client = get_supabase_client()
        result = client.table("users").insert({
            "email": email,
            "role": role
        }).execute()
        
        if result.data:
            logger.info(f"User created: {email}")
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to create user {email}: {e}")
        return None


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    try:
        client = get_supabase_client()
        result = client.table("users").select("*").eq("email", email).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get user {email}: {e}")
        return None
