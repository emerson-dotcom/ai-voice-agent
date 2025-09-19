from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from typing import Optional, Dict, Any
import logging
from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()

class AuthError(Exception):
    """Custom authentication error"""
    pass

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    Get the current authenticated user from the JWT token.
    This function validates the JWT token and returns user information.
    """
    try:
        # Extract the token from the Authorization header
        token = credentials.credentials
        
        # Verify the JWT token with Supabase
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = response.user
        
        # Get user role from our database
        user_result = supabase.table("users").select("role").eq("id", user.id).execute()
        
        if not user_result.data:
            # If user doesn't exist in our database, create them with default role
            supabase.table("users").insert({
                "id": user.id,
                "email": user.email,
                "role": "user"
            }).execute()
            user_role = "user"
        else:
            user_role = user_result.data[0]["role"]
        
        return {
            "id": user.id,
            "email": user.email,
            "role": user_role,
            "token": token
        }
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the current user and ensure they have admin role.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[Dict[str, Any]]:
    """
    Get the current user if authenticated, otherwise return None.
    This is useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None

def require_role(required_role: str):
    """
    Decorator factory for role-based access control.
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role} access required"
            )
        return current_user
    
    return role_checker

# Common role dependencies
require_admin = require_role("admin")
require_user = require_role("user")

# User info dependency for logging
async def get_user_info(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get user information for logging and audit purposes.
    """
    return {
        "user_id": current_user["id"],
        "user_email": current_user["email"],
        "user_role": current_user["role"]
    }
