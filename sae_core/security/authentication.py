"""
SAE Core Security - Authentication service.

This module provides authentication functionality with password hashing
and JWT token management.
"""

from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..config.settings import get_config
from ..persistence import User, Session as SessionModel, UserRepository, SessionRepository
from ..common.enums import generate_id, utc_now


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationService:
    """Authentication service for user login and session management."""
    
    def __init__(self, user_repo: UserRepository, session_repo: SessionRepository):
        """Initialize authentication service."""
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.config = get_config().auth
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: str) -> str:
        """Create a JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            return payload
        except JWTError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.active:
            return None
        return user
    
    def create_session(self, user: User) -> SessionModel:
        """Create a new session for a user."""
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)
        
        session = SessionModel(
            id=generate_id(),
            user_id=user.id,
            token=access_token,
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
            metadata_={"refresh_token": refresh_token}
        )
        
        return self.session_repo.create(session)
    
    def validate_session(self, token: str) -> Optional[User]:
        """Validate a session token and return the user."""
        payload = self.decode_token(token)
        if not payload:
            return None
        
        if payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Check if session exists and is not expired
        session = self.session_repo.get_by_token(token)
        if not session:
            return None
        
        if session.expires_at < datetime.utcnow():
            return None
        
        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.active:
            return None
        
        return user
    
    def refresh_session(self, refresh_token: str) -> Optional[SessionModel]:
        """Refresh a session using a refresh token."""
        payload = self.decode_token(refresh_token)
        if not payload:
            return None
        
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.active:
            return None
        
        # Create new session
        return self.create_session(user)
    
    def logout(self, token: str) -> bool:
        """Logout by deleting the session."""
        return self.session_repo.delete_by_token(token)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return self.session_repo.delete_expired()


def create_user(
    user_repo: UserRepository,
    username: str,
    email: str,
    password: str,
    roles: list[str],
    organization: Optional[str] = None
) -> User:
    """Create a new user with hashed password."""
    auth_service = AuthenticationService(user_repo, None)
    
    user = User(
        id=generate_id(),
        username=username,
        email=email,
        password_hash=auth_service.hash_password(password),
        roles=roles,
        organization=organization
    )
    
    return user_repo.create(user)
