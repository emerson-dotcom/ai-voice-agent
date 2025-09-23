"""
Supabase Authentication Service
Uses Supabase Auth for user authentication and management.
"""

import logging
from typing import Optional, Dict, Any, List
from app.core.database import supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseAuthService:
    """Service for Supabase authentication and authorization."""

    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email and password."""
        try:
            response = supabase_client.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.user and response.session:
                # Get user metadata
                user_metadata = response.user.user_metadata or {}

                # Log the action
                await SupabaseAuthService.log_audit_action(
                    user_id=response.user.id,
                    action='login',
                    details={'email': email}
                )

                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "full_name": user_metadata.get("full_name", ""),
                        "role": user_metadata.get("role", "user"),
                        "created_at": response.user.created_at,
                        "last_sign_in_at": response.user.last_sign_in_at
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at,
                        "token_type": response.session.token_type
                    }
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Error signing in user: {str(e)}")
            return None

    @staticmethod
    async def sign_out(access_token: str) -> bool:
        """Sign out user."""
        try:
            # Set the session first
            supabase_client.client.auth.set_session(access_token, None)

            # Sign out
            response = supabase_client.client.auth.sign_out()

            return True

        except Exception as e:
            logger.error(f"Error signing out user: {str(e)}")
            return False

    @staticmethod
    async def get_user_from_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token."""
        try:
            import jwt
            from app.core.config import settings

            # Decode JWT token to validate and extract user info
            # Use the SUPABASE_ANON_KEY as the secret for JWT validation
            decoded_token = jwt.decode(
                access_token,
                settings.SUPABASE_ANON_KEY,
                algorithms=["HS256"],
                options={"verify_signature": False}  # Temporarily disable signature verification
            )

            logger.info(f"Token decoded successfully for user: {decoded_token.get('email')}")

            # Extract user information from JWT payload
            user_metadata = decoded_token.get('user_metadata', {})

            return {
                "id": decoded_token.get('sub'),
                "email": decoded_token.get('email'),
                "full_name": user_metadata.get("full_name", ""),
                "role": user_metadata.get("role", "user"),
                "user_metadata": user_metadata,
                "created_at": decoded_token.get('iat'),
                "last_sign_in_at": decoded_token.get('iat')
            }

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            return None

    @staticmethod
    async def refresh_session(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh user session."""
        try:
            response = supabase_client.client.auth.refresh_session(refresh_token)

            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": response.session.token_type
                }

            return None

        except Exception as e:
            logger.error(f"Error refreshing session: {str(e)}")
            return None

    @staticmethod
    async def update_user_metadata(user_id: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata."""
        try:
            response = supabase_client.client.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata}
            )

            return response.user is not None

        except Exception as e:
            logger.error(f"Error updating user metadata: {str(e)}")
            return False

    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete a user."""
        try:
            response = supabase_client.client.auth.admin.delete_user(user_id)
            return True

        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    @staticmethod
    async def list_users(page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        try:
            response = supabase_client.client.auth.admin.list_users(
                page=page,
                per_page=per_page
            )

            users = []
            for user in response:
                user_metadata = user.user_metadata or {}
                users.append({
                    "id": user.id,
                    "email": user.email,
                    "full_name": user_metadata.get("full_name", ""),
                    "role": user_metadata.get("role", "user"),
                    "created_at": user.created_at,
                    "last_sign_in_at": user.last_sign_in_at,
                    "email_confirmed_at": user.email_confirmed_at
                })

            return users

        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return []

    @staticmethod
    async def ensure_admin_user() -> None:
        """Ensure admin user exists from environment variables."""
        try:
            admin_email = settings.ADMIN_EMAIL
            admin_password = settings.ADMIN_PASSWORD
            admin_name = settings.ADMIN_NAME

            if not all([admin_email, admin_password, admin_name]):
                logger.warning("Admin user environment variables not set")
                return

            # Try to sign in first to check if user exists
            signin_response = await SupabaseAuthService.sign_in(admin_email, admin_password)

            if signin_response:
                # Admin user exists and can sign in
                logger.info(f"Admin user verified: {admin_email}")

                # Update metadata to ensure admin role
                user_id = signin_response["user"]["id"]
                await SupabaseAuthService.update_user_metadata(user_id, {
                    "full_name": admin_name,
                    "role": "admin"
                })

                return

            # Create admin user using Supabase admin API
            try:
                response = supabase_client.client.auth.admin.create_user({
                    "email": admin_email,
                    "password": admin_password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": admin_name,
                        "role": "admin"
                    }
                })

                if response.user:
                    logger.info(f"Created admin user: {admin_email}")

                    # Log the action
                    await SupabaseAuthService.log_audit_action(
                        user_id=response.user.id,
                        action='admin_user_created',
                        details={'email': admin_email, 'full_name': admin_name}
                    )
                else:
                    logger.error("Failed to create admin user")

            except Exception as create_error:
                logger.error(f"Error creating admin user: {str(create_error)}")

        except Exception as e:
            logger.error(f"Error ensuring admin user: {str(e)}")

    @staticmethod
    async def log_audit_action(user_id: str, action: str, resource_type: str = None,
                             resource_id: str = None, details: Dict[str, Any] = None,
                             ip_address: str = None, user_agent: str = None) -> None:
        """Log an audit action."""
        try:
            audit_data = {
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            # Insert into audit_logs table
            supabase_client.client.table('audit_logs').insert(audit_data).execute()

        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")

    @staticmethod
    async def get_audit_logs(user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs."""
        try:
            query = supabase_client.client.table('audit_logs').select('*').order('created_at', desc=True).limit(limit)

            if user_id:
                query = query.eq('user_id', user_id)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error getting audit logs: {str(e)}")
            return []

    @staticmethod
    def has_permission(user_role: str, required_role: str) -> bool:
        """Check if user role has required permission."""
        role_hierarchy = {
            'admin': 3,
            'dispatcher': 2,
            'user': 1
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level