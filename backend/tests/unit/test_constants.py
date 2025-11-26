"""Tests for constants module."""

from app.constants import (
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    GOOGLE_API_TIMEOUT,
    GOOGLE_OAUTH_SCOPES,
    AUTH_CODE_MIN_LENGTH,
    AUTH_CODE_MAX_LENGTH,
    ERROR_AUTH_FAILED,
    ERROR_INVALID_CODE_FORMAT,
    CACHE_KEY_PREFIX_WIDGET,
    RATE_LIMIT_FAVICON_PROXY,
)


class TestConstants:
    """Test that constants are defined correctly."""

    def test_google_auth_url(self):
        """Test Google Auth URL is defined."""
        assert isinstance(GOOGLE_AUTH_URL, str)
        assert "google" in GOOGLE_AUTH_URL.lower()

    def test_google_token_url(self):
        """Test Google Token URL is defined."""
        assert isinstance(GOOGLE_TOKEN_URL, str)
        assert "google" in GOOGLE_TOKEN_URL.lower()

    def test_google_userinfo_url(self):
        """Test Google Userinfo URL is defined."""
        assert isinstance(GOOGLE_USERINFO_URL, str)
        assert "google" in GOOGLE_USERINFO_URL.lower()

    def test_google_api_timeout(self):
        """Test Google API timeout is a positive number."""
        assert isinstance(GOOGLE_API_TIMEOUT, (int, float))
        assert GOOGLE_API_TIMEOUT > 0

    def test_google_oauth_scopes(self):
        """Test Google OAuth scopes are defined."""
        assert isinstance(GOOGLE_OAUTH_SCOPES, str)
        assert "email" in GOOGLE_OAUTH_SCOPES

    def test_auth_code_min_length(self):
        """Test auth code min length."""
        assert isinstance(AUTH_CODE_MIN_LENGTH, int)
        assert AUTH_CODE_MIN_LENGTH > 0

    def test_auth_code_max_length(self):
        """Test auth code max length."""
        assert isinstance(AUTH_CODE_MAX_LENGTH, int)
        assert AUTH_CODE_MAX_LENGTH > AUTH_CODE_MIN_LENGTH

    def test_error_messages(self):
        """Test error messages are strings."""
        assert isinstance(ERROR_AUTH_FAILED, str)
        assert isinstance(ERROR_INVALID_CODE_FORMAT, str)

    def test_cache_key_prefix(self):
        """Test cache key prefix."""
        assert isinstance(CACHE_KEY_PREFIX_WIDGET, str)
        assert len(CACHE_KEY_PREFIX_WIDGET) > 0

    def test_rate_limits(self):
        """Test rate limit constants."""
        assert isinstance(RATE_LIMIT_FAVICON_PROXY, str)
        assert "/" in RATE_LIMIT_FAVICON_PROXY
