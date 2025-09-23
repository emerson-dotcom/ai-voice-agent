"""
API dependencies for authentication and authorization.
Provides dependency injection for route protection and user management.
"""

from fastapi import HTTPException, Header, Depends
from typing import Optional, Dict, Any
from app.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User data from Supabase Auth

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>" format
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme. Use Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token and get user
        user = await SupabaseAuthService.get_user_from_token(token)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to ensure current user is an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        Admin user data

    Raises:
        HTTPException: If user is not an admin
    """
    user_role = current_user.get('user_metadata', {}).get('role', 'user')

    if user_role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required"
        )

    return current_user


async def get_dispatcher_or_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to ensure current user is a dispatcher or admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User data if dispatcher or admin

    Raises:
        HTTPException: If user is not dispatcher or admin
    """
    user_role = current_user.get('user_metadata', {}).get('role', 'user')

    if user_role not in ['admin', 'dispatcher']:
        raise HTTPException(
            status_code=403,
            detail="Dispatcher or administrator privileges required"
        )

    return current_user


def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Optional dependency to get current user without requiring authentication.

    Args:
        authorization: Optional authorization header

    Returns:
        User data if authenticated, None otherwise
    """
    if not authorization:
        return None

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            return None

        # This should be made async in a real implementation
        # For now, return None to avoid blocking
        return None

    except (ValueError, Exception):
        return None