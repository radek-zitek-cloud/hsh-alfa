"""Application constants."""

# OAuth2 URLs
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# OAuth2 Scopes
GOOGLE_OAUTH_SCOPES = "openid email profile"

# HTTP Timeouts (in seconds)
GOOGLE_API_TIMEOUT = 10.0

# Authorization Code Validation
AUTH_CODE_MIN_LENGTH = 10
AUTH_CODE_MAX_LENGTH = 512

# Error Messages
ERROR_AUTH_FAILED = "Authentication failed"
ERROR_INVALID_CODE_FORMAT = "Invalid authorization code format"
ERROR_INVALID_CREDENTIALS = "Invalid authentication credentials"
ERROR_INVALID_TOKEN_PAYLOAD = "Invalid token payload"
ERROR_INVALID_USER_ID = "Invalid user ID in token"
ERROR_USER_NOT_FOUND = "User not found"
ERROR_USER_INACTIVE = "User account is inactive"
ERROR_AUTH_REQUIRED = "Authentication required"
ERROR_GOOGLE_OAUTH_NOT_CONFIGURED = "Google OAuth2 is not configured"
ERROR_INVALID_REQUEST = "Invalid request parameters"

# Cache Keys
CACHE_KEY_PREFIX_WIDGET = "widget:"

# Rate Limits
RATE_LIMIT_FAVICON_PROXY = "20/minute"
RATE_LIMIT_WIDGET_DATA = "60/minute"
RATE_LIMIT_WIDGET_REFRESH = "10/minute"
RATE_LIMIT_AUTH_CALLBACK = "10/minute"
RATE_LIMIT_AUTH_LOGIN = "5/minute"
RATE_LIMIT_AUTH_ME = "30/minute"
