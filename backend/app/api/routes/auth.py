"""
Authentication API endpoints.
Handles user authentication and session management using Supabase Auth.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, EmailStr
from app.services.supabase_auth_service import SupabaseAuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    role: str
    created_at: str
    last_sign_in_at: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response model."""
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str


class AuthResponse(BaseModel):
    """Authentication response model."""
    user: UserResponse
    session: SessionResponse


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


async def get_current_user(authorization: str = Header(None)):
    """Dependency to get current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    user = await SupabaseAuthService.get_user_from_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_client_info(request: Request):
    """Extract client information from request."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }


@router.post("/login", response_model=AuthResponse)
async def login(login_data: UserLogin, request: Request):
    """Login user with email and password."""
    try:
        client_info = get_client_info(request)

        result = await SupabaseAuthService.sign_in(
            email=login_data.email,
            password=login_data.password
        )

        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """Logout current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.split(" ")[1]

    try:
        success = await SupabaseAuthService.sign_out(token)
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/refresh", response_model=SessionResponse)
async def refresh_token(refresh_data: RefreshRequest):
    """Refresh access token."""
    try:
        result = await SupabaseAuthService.refresh_session(refresh_data.refresh_token)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    per_page: int = 50,
    admin_user: dict = Depends(require_admin)
):
    """List all users (admin only)."""
    try:
        users = await SupabaseAuthService.list_users(page=page, per_page=per_page)
        return users

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list users")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_user: dict = Depends(require_admin)):
    """Delete a user (admin only)."""
    try:
        success = await SupabaseAuthService.delete_user(user_id)

        if not success:
            raise HTTPException(status_code=404, detail="User not found or deletion failed")

        # Log the action
        await SupabaseAuthService.log_audit_action(
            user_id=admin_user["id"],
            action="user_deleted",
            resource_type="user",
            resource_id=user_id,
            details={"deleted_user_id": user_id}
        )

        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: dict,
    admin_user: dict = Depends(require_admin)
):
    """Update user role (admin only)."""
    try:
        new_role = role_data.get("role")
        if new_role not in ["user", "dispatcher", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")

        success = await SupabaseAuthService.update_user_metadata(user_id, {"role": new_role})

        if not success:
            raise HTTPException(status_code=404, detail="User not found or update failed")

        # Log the action
        await SupabaseAuthService.log_audit_action(
            user_id=admin_user["id"],
            action="user_role_updated",
            resource_type="user",
            resource_id=user_id,
            details={"new_role": new_role}
        )

        return {"message": f"User role updated to {new_role}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user role")


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs."""
    try:
        # Regular users can only see their own logs, admins can see all
        if current_user.get("role") != "admin":
            user_id = current_user["id"]

        logs = await SupabaseAuthService.get_audit_logs(user_id=user_id, limit=limit)
        return logs

    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")


@router.get("/check-auth")
async def check_auth_status(current_user: dict = Depends(get_current_user)):
    """Check if user is authenticated (for frontend auth checking)."""
    return {
        "authenticated": True,
        "user": current_user
    }