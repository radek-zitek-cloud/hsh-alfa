"""Authentication service for OAuth2 and JWT handling."""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import httpx
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User, UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations."""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self):
        """Initialize auth service."""
        if not settings.JWT_SECRET_KEY:
            logger.warning("JWT_SECRET_KEY not set, using SECRET_KEY as fallback")
            self.jwt_secret = settings.SECRET_KEY
        else:
            self.jwt_secret = settings.JWT_SECRET_KEY

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEY or SECRET_KEY must be set in environment")

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token.

        Args:
            data: Data to encode in the token

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_secret,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Google

        Returns:
            Access token or None if exchange failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
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
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
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
            user.last_login = datetime.utcnow()
            # Update user info in case it changed
            user.name = google_user_info.get("name")
            user.picture = google_user_info.get("picture")
            user.email = email
            await db.commit()
            await db.refresh(user)
            logger.info(f"User logged in: {email}")
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
                last_login=datetime.utcnow()
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New user created: {email}")
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
