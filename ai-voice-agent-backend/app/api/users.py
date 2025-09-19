from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models.schemas import APIResponse, UserRole
from app.core.database import get_supabase_client
from app.core.auth import get_current_user, get_current_admin_user, get_user_info
from supabase import Client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/users/me", response_model=APIResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get the current user's profile information."""
    try:
        # Get full user profile from database
        result = supabase.table("users").select("*").eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_profile = result.data[0]
        
        return APIResponse(
            success=True,
            message="User profile retrieved successfully",
            data=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/me", response_model=APIResponse)
async def update_current_user_profile(
    profile_update: dict,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update the current user's profile information."""
    try:
        # Only allow updating certain fields
        allowed_fields = ["email"]  # Add more fields as needed
        update_data = {k: v for k, v in profile_update.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update user profile in database
        result = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update user profile")
        
        logger.info(f"User profile updated: {current_user['id']}")
        
        return APIResponse(
            success=True,
            message="User profile updated successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=APIResponse)
async def get_all_users(
    admin_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all users (admin only)."""
    try:
        result = supabase.table("users").select("*").order("created_at", desc=True).execute()
        
        return APIResponse(
            success=True,
            message="Users retrieved successfully",
            data=result.data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=APIResponse)
async def get_user_by_id(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific user by ID (admin only)."""
    try:
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return APIResponse(
            success=True,
            message="User retrieved successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}/role", response_model=APIResponse)
async def update_user_role(
    user_id: str,
    role_update: dict,
    admin_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a user's role (admin only)."""
    try:
        new_role = role_update.get("role")
        
        if new_role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'")
        
        # Prevent admin from changing their own role
        if user_id == admin_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        
        # Update user role
        result = supabase.table("users").update({"role": new_role}).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User role updated: {user_id} -> {new_role} by {admin_user['id']}")
        
        return APIResponse(
            success=True,
            message="User role updated successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: str,
    admin_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a user (admin only)."""
    try:
        # Prevent admin from deleting themselves
        if user_id == admin_user["id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Check if user exists
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user
        supabase.table("users").delete().eq("id", user_id).execute()
        
        logger.info(f"User deleted: {user_id} by {admin_user['id']}")
        
        return APIResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/stats", response_model=APIResponse)
async def get_user_stats(
    admin_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get user statistics (admin only)."""
    try:
        # Get total users
        total_users_result = supabase.table("users").select("id", count="exact").execute()
        total_users = total_users_result.count or 0
        
        # Get admin users
        admin_users_result = supabase.table("users").select("id", count="exact").eq("role", "admin").execute()
        admin_users = admin_users_result.count or 0
        
        # Get regular users
        regular_users = total_users - admin_users
        
        stats = {
            "total_users": total_users,
            "admin_users": admin_users,
            "regular_users": regular_users
        }
        
        return APIResponse(
            success=True,
            message="User statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
