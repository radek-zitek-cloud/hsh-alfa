"""Authentication API endpoints."""
from typing import Optional
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import settings
from app.logging_config import get_logger
from app.models.user import TokenResponse, UserResponse
from app.services.auth_service import auth_service, mask_email
from app.services.database import get_db
from app.services.rate_limit import limiter
from app.api.dependencies import get_current_user, require_auth, security
from app.models.user import User
from app.constants import (
    GOOGLE_AUTH_URL,
    GOOGLE_OAUTH_SCOPES,
    AUTH_CODE_MIN_LENGTH,
    AUTH_CODE_MAX_LENGTH,
    ERROR_AUTH_FAILED,
    ERROR_INVALID_CODE_FORMAT,
    ERROR_GOOGLE_OAUTH_NOT_CONFIGURED,
    ERROR_INVALID_REQUEST,
    RATE_LIMIT_AUTH_CALLBACK,
    RATE_LIMIT_AUTH_LOGIN,
    RATE_LIMIT_AUTH_ME,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleAuthURL(BaseModel):
    """Response model for Google OAuth URL."""
    auth_url: str


class CallbackRequest(BaseModel):
    """Request model for OAuth callback."""
    code: str
    state: Optional[str] = None

    def validate_code(self) -> bool:
        """Validate authorization code format and length.

        Returns:
            True if code is valid, False otherwise
        """
        # Authorization codes should be non-empty and reasonable length
        # Google codes are URL-safe base64 encoded and can contain: alphanumeric, hyphens, underscores, slashes, and percent-encoding
        if not self.code or len(self.code) < AUTH_CODE_MIN_LENGTH or len(self.code) > AUTH_CODE_MAX_LENGTH:
            return False
        # Check for URL-safe pattern (allow alphanumeric, hyphens, underscores, slashes, and percent-encoding)
        return all(c.isalnum() or c in '-_/%' for c in self.code)


@router.get("/google/url", response_model=GoogleAuthURL)
@limiter.limit(RATE_LIMIT_AUTH_LOGIN)
async def get_google_auth_url(request: Request):
    """Get Google OAuth2 authorization URL with CSRF protection.

    Returns:
        GoogleAuthURL: Object containing the authorization URL with state parameter
    """
    logger.info(
        "Google OAuth URL requested",
        extra={
            "client_host": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
    )

    if not settings.GOOGLE_CLIENT_ID:
        logger.error(
            "Google OAuth not configured",
            extra={"client_id_present": bool(settings.GOOGLE_CLIENT_ID)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_GOOGLE_OAUTH_NOT_CONFIGURED
        )

    # Generate state token for CSRF protection
    state = auth_service.generate_state_token()
    logger.debug(
        "Generated state token for OAuth flow",
        extra={"state_length": len(state)}
    )

    # Build Google OAuth2 authorization URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_OAUTH_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,  # CSRF protection
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    return GoogleAuthURL(auth_url=auth_url)


@router.post("/callback", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH_CALLBACK)
async def oauth_callback(
    request: Request,
    callback_request: CallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth2 callback and create session with CSRF validation.

    Args:
        callback_request: Callback request with authorization code and state
        db: Database session

    Returns:
        TokenResponse: JWT token and user info

    Raises:
        HTTPException: If authentication fails or state validation fails
    """
    logger.info(
        "OAuth callback received",
        extra={
            "state_present": bool(callback_request.state),
            "code_length": len(callback_request.code) if callback_request.code else 0,
            "client_host": request.client.host if request.client else "unknown",
        }
    )

    # Validate state token for CSRF protection
    if not callback_request.state or not auth_service.validate_state_token(callback_request.state):
        # Log detailed information for security monitoring without revealing to user
        logger.warning(
            "Invalid or missing state token in OAuth callback - possible CSRF attack",
            extra={
                "state_present": bool(callback_request.state),
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_REQUEST
        )

    # Validate authorization code format
    if not callback_request.validate_code():
        logger.warning(
            "Invalid authorization code format in OAuth callback",
            extra={
                "code_length": len(callback_request.code),
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_CODE_FORMAT
        )

    # Authenticate user with authorization code
    logger.debug("Authenticating user with OAuth code")
    user = await auth_service.authenticate_user(db, callback_request.code)
    if not user:
        logger.warning(
            "OAuth authentication failed - user creation or token exchange failed",
            extra={
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_AUTH_FAILED
        )

    # Create JWT token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    logger.info(
        "User authenticated successfully via OAuth",
        extra={
            "user_id": user.id,
            "user_email": mask_email(user.email),
            "is_new_user": user.created_at == user.last_login if user.last_login else True,
        }
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
@limiter.limit(RATE_LIMIT_AUTH_ME)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(require_auth)
):
    """Get current authenticated user information.

    Args:
        request: HTTP request
        current_user: Current authenticated user

    Returns:
        UserResponse: Current user information
    """
    logger.debug(
        "User info requested",
        extra={"user_id": current_user.id, "user_email": mask_email(current_user.email)}
    )

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
async def logout(
    current_user: User = Depends(require_auth),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Logout current user and blacklist their JWT token.

    Args:
        current_user: Current authenticated user
        credentials: HTTP authorization credentials

    Returns:
        Success message

    Raises:
        HTTPException: If token blacklisting fails
    """
    if credentials:
        token = credentials.credentials
        token_blacklisted = auth_service.blacklist_token(token)
        if token_blacklisted:
            logger.info(
                "User logged out and token blacklisted",
                extra={
                    "user_id": current_user.id,
                    "user_email": mask_email(current_user.email),
                }
            )
        else:
            logger.warning(
                "User logged out but token blacklisting failed",
                extra={
                    "user_id": current_user.id,
                    "user_email": mask_email(current_user.email),
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete logout"
            )
    else:
        logger.info(
            "User logged out",
            extra={
                "user_id": current_user.id,
                "user_email": mask_email(current_user.email),
            }
        )

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
    logger.debug(
        "Authentication check",
        extra={"authenticated": current_user is not None}
    )

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
