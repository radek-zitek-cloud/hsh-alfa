"""Authentication service for OAuth2 and JWT handling."""

import hashlib
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import ADMIN_EMAIL, GOOGLE_API_TIMEOUT, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL
from app.logging_config import get_logger
from app.models.user import User, UserCreate, UserRole

logger = get_logger(__name__)


def mask_email(email: str) -> str:
    """Mask email address for logging to protect PII.

    Args:
        email: Email address to mask

    Returns:
        Masked email with SHA-256 hash prefix
    """
    if not email:
        return "unknown"
    # Use first 16 characters of SHA-256 hash for better entropy and reduced collision risk
    email_hash = hashlib.sha256(email.encode()).hexdigest()[:16]
    return f"user_{email_hash}"


class AuthService:
    """Service for handling authentication operations."""

    # In-memory store for OAuth state tokens (in production, use Redis)
    # Format: {state_token: expiration_timestamp}
    _state_store: Dict[str, float] = {}
    _state_lock = threading.Lock()

    # In-memory store for blacklisted tokens (in production, use Redis)
    # Format: {token_jti: expiration_timestamp}
    _token_blacklist: Dict[str, float] = {}
    _blacklist_lock = threading.Lock()

    def __init__(self):
        """Initialize auth service."""
        if not settings.JWT_SECRET_KEY:
            logger.warning(
                "JWT_SECRET_KEY not set, using SECRET_KEY as fallback",
                extra={"operation": "auth_init", "config_issue": "jwt_secret_missing"},
            )
            self.jwt_secret = settings.SECRET_KEY
        else:
            self.jwt_secret = settings.JWT_SECRET_KEY

        if not self.jwt_secret:
            logger.error(
                "No JWT secret configured",
                extra={"operation": "auth_init_failed", "error": "no_secret_configured"},
            )
            raise ValueError("JWT_SECRET_KEY or SECRET_KEY must be set in environment")

        logger.debug(
            "Auth service initialized",
            extra={
                "operation": "auth_init",
                "jwt_algorithm": settings.JWT_ALGORITHM,
                "expiration_hours": settings.JWT_EXPIRATION_HOURS,
            },
        )

    def generate_state_token(self) -> str:
        """Generate a secure random state token for CSRF protection.

        Returns:
            Random state token
        """
        state = secrets.token_urlsafe(32)
        # Store with 10-minute expiration
        expiration = datetime.now(timezone.utc).timestamp() + 600
        with self._state_lock:
            self._state_store[state] = expiration
        logger.debug(
            "OAuth state token generated",
            extra={
                "operation": "state_token_generated",
                "expiration_seconds": 600,
                "state_store_size": len(self._state_store),
            },
        )
        return state

    def validate_state_token(self, state: str) -> bool:
        """Validate OAuth state token to prevent CSRF attacks.

        Args:
            state: State token to validate

        Returns:
            True if valid, False otherwise
        """
        with self._state_lock:
            if not state or state not in self._state_store:
                logger.warning(
                    "Invalid or missing OAuth state token",
                    extra={
                        "operation": "state_token_validation_failed",
                        "reason": "token_not_found",
                    },
                )
                return False

            expiration = self._state_store[state]
            now = datetime.now(timezone.utc).timestamp()

            # Check if expired
            if now > expiration:
                del self._state_store[state]
                logger.warning(
                    "OAuth state token expired",
                    extra={"operation": "state_token_validation_failed", "reason": "token_expired"},
                )
                return False

            # Valid token - remove it (one-time use)
            del self._state_store[state]
            logger.debug(
                "OAuth state token validated successfully",
                extra={"operation": "state_token_validated"},
            )
            return True

    def _cleanup_expired_states(self):
        """Clean up expired state tokens from store."""
        now = datetime.now(timezone.utc).timestamp()
        with self._state_lock:
            expired_states = [state for state, exp in self._state_store.items() if now > exp]
            for state in expired_states:
                del self._state_store[state]
            if expired_states:
                logger.debug(
                    "Expired state tokens cleaned up",
                    extra={
                        "operation": "state_cleanup",
                        "cleaned_count": len(expired_states),
                        "remaining_states": len(self._state_store),
                    },
                )

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
        to_encode.update({"exp": expire, "jti": jti, "iat": datetime.now(timezone.utc).timestamp()})

        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=settings.JWT_ALGORITHM)
        logger.debug(
            "JWT access token created",
            extra={
                "operation": "token_created",
                "jti": jti,
                "expiration_hours": settings.JWT_EXPIRATION_HOURS,
                "subject": data.get("sub", "unknown"),
            },
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
            payload = jwt.decode(token, self.jwt_secret, algorithms=[settings.JWT_ALGORITHM])

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning(
                    "Attempted use of blacklisted token",
                    extra={
                        "operation": "token_verification_failed",
                        "reason": "token_blacklisted",
                        "jti": jti,
                        "subject": payload.get("sub", "unknown"),
                    },
                )
                return None

            logger.debug(
                "JWT token verified successfully",
                extra={
                    "operation": "token_verified",
                    "jti": jti,
                    "subject": payload.get("sub", "unknown"),
                },
            )
            return payload
        except JWTError as e:
            logger.warning(
                "JWT verification failed",
                extra={
                    "operation": "token_verification_failed",
                    "reason": "invalid_jwt",
                    "error_type": type(e).__name__,
                },
            )
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
                options={"verify_exp": False},  # Allow decoding expired tokens
            )

            jti = payload.get("jti")
            exp = payload.get("exp")

            if not jti or not exp:
                logger.warning(
                    "Cannot blacklist token - missing jti or exp",
                    extra={
                        "operation": "token_blacklist_failed",
                        "reason": "missing_claims",
                        "subject": payload.get("sub", "unknown"),
                    },
                )
                return False

            # Store until token expiration
            with self._blacklist_lock:
                self._token_blacklist[jti] = float(exp)
            logger.info(
                "Token blacklisted for logout",
                extra={
                    "operation": "token_blacklisted",
                    "jti": jti,
                    "subject": payload.get("sub", "unknown"),
                },
            )
            return True
        except JWTError as e:
            logger.error(
                "Failed to blacklist token",
                extra={"operation": "token_blacklist_failed", "error_type": type(e).__name__},
                exc_info=True,
            )
            return False

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted.

        Args:
            jti: Token unique identifier

        Returns:
            True if blacklisted, False otherwise
        """
        with self._blacklist_lock:
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
        with self._blacklist_lock:
            expired_tokens = [jti for jti, exp in self._token_blacklist.items() if now > exp]
            for jti in expired_tokens:
                del self._token_blacklist[jti]
            if expired_tokens:
                logger.debug(
                    "Expired blacklisted tokens cleaned up",
                    extra={
                        "operation": "blacklist_cleanup",
                        "cleaned_count": len(expired_tokens),
                        "remaining_blacklisted": len(self._token_blacklist),
                    },
                )

    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Access token or None if exchange failed
        """
        try:
            logger.debug(
                "Exchanging authorization code for token",
                extra={
                    "operation": "oauth_code_exchange_attempt",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
            )
            async with httpx.AsyncClient(timeout=GOOGLE_API_TIMEOUT) as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                )
                response.raise_for_status()
                token_data = response.json()
                logger.info(
                    "Authorization code exchanged for token successfully",
                    extra={
                        "operation": "oauth_code_exchanged",
                        "token_type": token_data.get("token_type", "unknown"),
                    },
                )
                return token_data.get("access_token")
        except httpx.HTTPError as e:
            logger.error(
                "Failed to exchange code for token",
                extra={"operation": "oauth_code_exchange_failed", "error_type": type(e).__name__},
                exc_info=True,
            )
            return None

    async def get_google_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user info from Google using access token.

        Args:
            access_token: Google access token

        Returns:
            User info dict or None if request failed
        """
        try:
            logger.debug(
                "Fetching Google user info", extra={"operation": "oauth_userinfo_fetch_attempt"}
            )
            async with httpx.AsyncClient(timeout=GOOGLE_API_TIMEOUT) as client:
                response = await client.get(
                    GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                user_info = response.json()
                logger.info(
                    "Google user info retrieved successfully",
                    extra={
                        "operation": "oauth_userinfo_fetched",
                        "user_email": mask_email(user_info.get("email", "")),
                    },
                )
                return user_info
        except httpx.HTTPError as e:
            logger.error(
                "Failed to get user info from Google",
                extra={"operation": "oauth_userinfo_fetch_failed", "error_type": type(e).__name__},
                exc_info=True,
            )
            return None

    async def get_or_create_user(
        self, db: AsyncSession, google_user_info: Dict[str, Any]
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
            logger.error(
                "Missing google_id or email in user info",
                extra={"operation": "user_creation_failed", "reason": "missing_claims"},
            )
            return None

        # Try to find existing user by google_id
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if user:
            # Update last login time
            user.last_login = datetime.now(timezone.utc)
            # Update user info in case it changed
            user.name = google_user_info.get("name")
            user.picture = google_user_info.get("picture")
            user.email = email
            # Set admin role for specific email
            if email == ADMIN_EMAIL:
                user.role = UserRole.ADMIN.value
            await db.commit()
            await db.refresh(user)
            logger.info(
                "Existing user logged in",
                extra={
                    "operation": "user_login",
                    "user_id": user.id,
                    "user_email": mask_email(email),
                    "action": "login",
                },
            )
            return user

        # Create new user
        try:
            user_create = UserCreate(
                email=email,
                google_id=google_id,
                name=google_user_info.get("name"),
                picture=google_user_info.get("picture"),
            )

            # Determine role based on email
            role = UserRole.ADMIN.value if email == ADMIN_EMAIL else UserRole.USER.value

            user = User(
                email=user_create.email,
                google_id=user_create.google_id,
                name=user_create.name,
                picture=user_create.picture,
                role=role,
                last_login=datetime.now(timezone.utc),
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(
                "New user created",
                extra={
                    "operation": "user_creation",
                    "user_id": user.id,
                    "user_email": mask_email(email),
                    "action": "signup",
                },
            )
            return user
        except Exception as e:
            logger.error(
                "Failed to create user in database",
                extra={
                    "operation": "user_creation_failed",
                    "user_email": mask_email(email),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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
        result = await db.execute(select(User).where(User.id == user_id))
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
