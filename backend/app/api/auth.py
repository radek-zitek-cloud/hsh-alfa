"""Authentication API endpoints."""
import logging
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import settings
from app.models.user import TokenResponse, UserResponse
from app.services.auth_service import auth_service
from app.services.database import get_db
from app.api.dependencies import get_current_user, require_auth
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleAuthURL(BaseModel):
    """Response model for Google OAuth URL."""
    auth_url: str


class CallbackRequest(BaseModel):
    """Request model for OAuth callback."""
    code: str


@router.get("/google/url", response_model=GoogleAuthURL)
async def get_google_auth_url():
    """Get Google OAuth2 authorization URL.

    Returns:
        GoogleAuthURL: Object containing the authorization URL
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth2 is not configured"
        )

    # Build Google OAuth2 authorization URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return GoogleAuthURL(auth_url=auth_url)


@router.post("/callback", response_model=TokenResponse)
async def oauth_callback(
    callback_request: CallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth2 callback and create session.

    Args:
        callback_request: Callback request with authorization code
        db: Database session

    Returns:
        TokenResponse: JWT token and user info

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user with authorization code
    user = await auth_service.authenticate_user(db, callback_request.code)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    # Create JWT token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    # Create user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(require_auth)
):
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@router.post("/logout")
async def logout(current_user: User = Depends(require_auth)):
    """Logout current user.

    Note: Since we're using JWT tokens, actual logout is handled on the client side
    by removing the token. This endpoint exists for consistency and future extensions.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}


@router.get("/check")
async def check_auth(
    current_user: Optional[User] = Depends(get_current_user)
):
    """Check if user is authenticated.

    Args:
        current_user: Current user if authenticated

    Returns:
        Authentication status
    """
    return {
        "authenticated": current_user is not None,
        "user": UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            picture=current_user.picture,
            is_active=current_user.is_active,
            created_at=current_user.created_at.isoformat(),
            last_login=current_user.last_login.isoformat() if current_user.last_login else None
        ) if current_user else None
    }
