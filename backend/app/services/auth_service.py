"""Authentication service for OAuth2 and JWT handling."""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import httpx
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserCreate
from app.constants import (
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_API_TIMEOUT,
)

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """Mask email address for logging to protect PII.

    Args:
        email: Email address to mask

    Returns:
        Masked email with SHA-256 hash prefix
    """
    if not email:
        return "unknown"
    # Use first 8 characters of SHA-256 hash for identification without exposing PII
    email_hash = hashlib.sha256(email.encode()).hexdigest()[:8]
    return f"user_{email_hash}"


class AuthService:
    """Service for handling authentication operations."""

    # In-memory store for OAuth state tokens (in production, use Redis)
    # Format: {state_token: expiration_timestamp}
    _state_store: Dict[str, float] = {}

    # In-memory store for blacklisted tokens (in production, use Redis)
    # Format: {token_jti: expiration_timestamp}
    _token_blacklist: Dict[str, float] = {}

    def __init__(self):
        """Initialize auth service."""
        if not settings.JWT_SECRET_KEY:
            logger.warning("JWT_SECRET_KEY not set, using SECRET_KEY as fallback")
            self.jwt_secret = settings.SECRET_KEY
        else:
            self.jwt_secret = settings.JWT_SECRET_KEY

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEY or SECRET_KEY must be set in environment")

    def generate_state_token(self) -> str:
        """Generate a secure random state token for CSRF protection.

        Returns:
            Random state token
        """
        state = secrets.token_urlsafe(32)
        # Store with 10-minute expiration
        expiration = datetime.now(timezone.utc).timestamp() + 600
        self._state_store[state] = expiration
        # Clean up expired tokens
        self._cleanup_expired_states()
        return state

    def validate_state_token(self, state: str) -> bool:
        """Validate OAuth state token to prevent CSRF attacks.

        Args:
            state: State token to validate

        Returns:
            True if valid, False otherwise
        """
        if not state or state not in self._state_store:
            return False

        expiration = self._state_store[state]
        now = datetime.now(timezone.utc).timestamp()

        # Check if expired
        if now > expiration:
            del self._state_store[state]
            return False

        # Valid token - remove it (one-time use)
        del self._state_store[state]
        return True

    def _cleanup_expired_states(self):
        """Clean up expired state tokens from store."""
        now = datetime.now(timezone.utc).timestamp()
        expired_states = [
            state for state, exp in self._state_store.items()
            if now > exp
        ]
        for state in expired_states:
            del self._state_store[state]

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token with unique identifier.

        Args:
            data: Data to encode in the token

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        # Add unique identifier for token blacklisting
        jti = secrets.token_urlsafe(16)
        to_encode.update({
            "exp": expire,
            "jti": jti,
            "iat": datetime.now(timezone.utc).timestamp()
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_secret,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token, checking blacklist.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload or None if invalid or blacklisted
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning(f"Attempted use of blacklisted token")
                return None

            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    def blacklist_token(self, token: str) -> bool:
        """Blacklist a JWT token to prevent its use after logout.

        Args:
            token: JWT token to blacklist

        Returns:
            True if successfully blacklisted, False otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False}  # Allow decoding expired tokens
            )

            jti = payload.get("jti")
            exp = payload.get("exp")

            if not jti or not exp:
                return False

            # Store until token expiration
            self._token_blacklist[jti] = float(exp)
            self._cleanup_expired_blacklist()
            return True
        except JWTError as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted.

        Args:
            jti: Token unique identifier

        Returns:
            True if blacklisted, False otherwise
        """
        if jti not in self._token_blacklist:
            return False

        # Check if still valid (not expired)
        exp = self._token_blacklist[jti]
        now = datetime.now(timezone.utc).timestamp()

        if now > exp:
            # Token expired, remove from blacklist
            del self._token_blacklist[jti]
            return False

        return True

    def _cleanup_expired_blacklist(self):
        """Clean up expired tokens from blacklist."""
        now = datetime.now(timezone.utc).timestamp()
        expired_tokens = [
            jti for jti, exp in self._token_blacklist.items()
            if now > exp
        ]
        for jti in expired_tokens:
            del self._token_blacklist[jti]

    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Access token or None if exchange failed
        """
        try:
            async with httpx.AsyncClient(timeout=GOOGLE_API_TIMEOUT) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    }
                )
                response.raise_for_status()
                token_data = response.json()
                return token_data.get("access_token")
        except httpx.HTTPError as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None

    async def get_google_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Google using access token.

        Args:
            access_token: Google access token

        Returns:
            User info dict or None if request failed
        """
        try:
            async with httpx.AsyncClient(timeout=GOOGLE_API_TIMEOUT) as client:
                response = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def get_or_create_user(
        self,
        db: AsyncSession,
        google_user_info: Dict[str, Any]
    ) -> Optional[User]:
        """Get existing user or create new one from Google user info.

        Args:
            db: Database session
            google_user_info: User info from Google

        Returns:
            User object or None if creation failed
        """
        google_id = google_user_info.get("id")
        email = google_user_info.get("email")

        if not google_id or not email:
            logger.error("Missing google_id or email in user info")
            return None

        # Try to find existing user by google_id
        result = await db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update last login time
            user.last_login = datetime.now(timezone.utc)
            # Update user info in case it changed
            user.name = google_user_info.get("name")
            user.picture = google_user_info.get("picture")
            user.email = email
            await db.commit()
            await db.refresh(user)
            logger.info(f"User logged in: {mask_email(email)}")
            return user

        # Create new user
        try:
            user_create = UserCreate(
                email=email,
                google_id=google_id,
                name=google_user_info.get("name"),
                picture=google_user_info.get("picture")
            )

            user = User(
                email=user_create.email,
                google_id=user_create.google_id,
                name=user_create.name,
                picture=user_create.picture,
                last_login=datetime.now(timezone.utc)
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user created: {mask_email(email)}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            await db.rollback()
            return None

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User object or None if not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, db: AsyncSession, code: str) -> Optional[User]:
        """Authenticate user using OAuth2 authorization code.

        Args:
            db: Database session
            code: Authorization code from Google

        Returns:
            User object or None if authentication failed
        """
        # Exchange code for access token
        access_token = await self.exchange_code_for_token(code)
        if not access_token:
            logger.error("Failed to get access token")
            return None

        # Get user info from Google
        google_user_info = await self.get_google_user_info(access_token)
        if not google_user_info:
            logger.error("Failed to get user info")
            return None

        # Get or create user in database
        user = await self.get_or_create_user(db, google_user_info)
        return user


# Global auth service instance
auth_service = AuthService()
