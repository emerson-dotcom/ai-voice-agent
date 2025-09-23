"""
Authentication Service
Handles user authentication, session management, and authorization.
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.core.database import supabase_client
from app.core.config import settings
import bcrypt

logger = logging.getLogger(__name__)


class AuthService:
    """Service for user authentication and authorization."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a session token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    async def create_user(email: str, password: str, full_name: str, role: str = 'user') -> Dict[str, Any]:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = await AuthService.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")

            # Hash password
            password_hash = AuthService.hash_password(password)

            # Create user record
            user_data = {
                'email': email,
                'password_hash': password_hash,
                'full_name': full_name,
                'role': role,
                'is_active': True
            }

            response = supabase_client.client.table('users').insert(user_data).execute()
            if not response.data:
                raise Exception("Failed to create user")

            user = response.data[0]

            # Log the action
            await AuthService.log_audit_action(
                user_id=user['id'],
                action='user_created',
                details={'email': email, 'role': role}
            )

            # Remove password hash from response
            user.pop('password_hash', None)
            return user

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            response = supabase_client.client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            response = supabase_client.client.table('users').select('*').eq('id', user_id).execute()
            if response.data:
                user = response.data[0]
                user.pop('password_hash', None)  # Remove password hash
                return user
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        try:
            user = await AuthService.get_user_by_email(email)
            if not user:
                return None

            if not user.get('is_active'):
                raise ValueError("User account is inactive")

            if not AuthService.verify_password(password, user['password_hash']):
                return None

            # Update last login
            await supabase_client.client.table('users').update({
                'last_login': datetime.utcnow().isoformat()
            }).eq('id', user['id']).execute()

            # Remove password hash from response
            user.pop('password_hash', None)
            return user

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None

    @staticmethod
    async def create_session(user_id: str, user_agent: str = None, ip_address: str = None) -> str:
        """Create a new user session."""
        try:
            # Generate session token
            token = AuthService.generate_session_token()
            token_hash = AuthService.hash_token(token)

            # Set expiration (24 hours from now)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            # Create session record
            session_data = {
                'user_id': user_id,
                'token_hash': token_hash,
                'expires_at': expires_at.isoformat(),
                'user_agent': user_agent,
                'ip_address': ip_address
            }

            response = supabase_client.client.table('user_sessions').insert(session_data).execute()
            if not response.data:
                raise Exception("Failed to create session")

            # Log the action
            await AuthService.log_audit_action(
                user_id=user_id,
                action='login',
                details={'ip_address': ip_address, 'user_agent': user_agent}
            )

            return token

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise

    @staticmethod
    async def validate_session(token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token and return user info."""
        try:
            token_hash = AuthService.hash_token(token)

            # Get session
            response = supabase_client.client.table('user_sessions').select('*').eq('token_hash', token_hash).execute()
            if not response.data:
                return None

            session = response.data[0]

            # Check if session is expired
            expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                # Delete expired session
                await AuthService.delete_session(token)
                return None

            # Update last used timestamp
            await supabase_client.client.table('user_sessions').update({
                'last_used': datetime.utcnow().isoformat()
            }).eq('id', session['id']).execute()

            # Get user info
            user = await AuthService.get_user_by_id(session['user_id'])
            if not user or not user.get('is_active'):
                return None

            return user

        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            return None

    @staticmethod
    async def delete_session(token: str) -> bool:
        """Delete a session token."""
        try:
            token_hash = AuthService.hash_token(token)
            response = supabase_client.client.table('user_sessions').delete().eq('token_hash', token_hash).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False

    @staticmethod
    async def logout_user(user_id: str, token: str = None) -> bool:
        """Logout user by deleting session(s)."""
        try:
            if token:
                # Delete specific session
                success = await AuthService.delete_session(token)
            else:
                # Delete all sessions for user
                response = supabase_client.client.table('user_sessions').delete().eq('user_id', user_id).execute()
                success = True

            # Log the action
            await AuthService.log_audit_action(
                user_id=user_id,
                action='logout',
                details={'all_sessions': token is None}
            )

            return success

        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            return False

    @staticmethod
    async def clean_expired_sessions() -> int:
        """Clean up expired sessions."""
        try:
            response = supabase_client.client.rpc('clean_expired_sessions').execute()
            count = response.data or 0
            logger.info(f"Cleaned up {count} expired sessions")
            return count
        except Exception as e:
            logger.error(f"Error cleaning expired sessions: {str(e)}")
            return 0

    @staticmethod
    async def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
        """Get active sessions for a user."""
        try:
            response = supabase_client.client.table('user_sessions').select('*').eq('user_id', user_id).execute()
            sessions = response.data or []

            # Filter out expired sessions
            current_time = datetime.utcnow()
            active_sessions = []

            for session in sessions:
                expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
                if expires_at > current_time.replace(tzinfo=expires_at.tzinfo):
                    # Remove sensitive data
                    session.pop('token_hash', None)
                    active_sessions.append(session)

            return active_sessions

        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []

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
    async def ensure_admin_user() -> None:
        """Ensure admin user exists from environment variables."""
        try:
            admin_email = settings.ADMIN_EMAIL
            admin_password = settings.ADMIN_PASSWORD
            admin_name = settings.ADMIN_NAME

            if not all([admin_email, admin_password, admin_name]):
                logger.warning("Admin user environment variables not set")
                return

            # Check if admin user already exists
            existing_admin = await AuthService.get_user_by_email(admin_email)
            if existing_admin:
                logger.info(f"Admin user already exists: {admin_email}")
                return

            # Create admin user
            admin_user = await AuthService.create_user(
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
                role='admin'
            )

            logger.info(f"Created admin user: {admin_email}")

        except Exception as e:
            logger.error(f"Error ensuring admin user: {str(e)}")

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