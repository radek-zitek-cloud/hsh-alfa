"""Tests for security-related configuration validation."""

import os
from unittest.mock import patch

import pytest

from app.config import Settings


def test_secret_key_requires_minimum_length():
    """SECRET_KEY shorter than 32 characters should be rejected."""
    with pytest.raises(ValueError):
        Settings(SECRET_KEY="too-short-secret")


def test_secret_key_rejects_placeholders():
    """Placeholder SECRET_KEY values must be blocked."""
    with pytest.raises(ValueError):
        Settings(SECRET_KEY="change-this-in-production")


def test_secret_key_accepts_strong_value():
    """A sufficiently long random-looking SECRET_KEY should be accepted."""
    key = "a-secure-secret-key-with-sufficient-length-123456"
    settings = Settings(SECRET_KEY=key)
    assert settings.SECRET_KEY == key


def test_cors_wildcard_rejected():
    """Wildcard CORS origins should be rejected and replaced with localhost defaults."""
    with patch.dict(
        os.environ,
        {"CORS_ORIGINS": "*", "SECRET_KEY": "a-secure-secret-key-with-sufficient-length-123456"},
    ):
        settings = Settings()
        # Verify wildcard is not in the list
        assert "*" not in settings.CORS_ORIGINS
        # Verify localhost defaults are used instead
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS


def test_cors_wildcard_with_whitespace_rejected():
    """Wildcard CORS origins with whitespace should be trimmed and rejected."""
    with patch.dict(
        os.environ,
        {"CORS_ORIGINS": " * ", "SECRET_KEY": "a-secure-secret-key-with-sufficient-length-123456"},
    ):
        settings = Settings()
        # Verify wildcard (even with whitespace) is not in the list
        assert "*" not in settings.CORS_ORIGINS
        assert " * " not in settings.CORS_ORIGINS
        # Verify localhost defaults are used instead
        assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_cors_explicit_origins_preserved():
    """Explicitly set CORS origins should be preserved correctly."""
    test_origins = "https://home.example.com,http://localhost:3000"
    with patch.dict(
        os.environ,
        {
            "CORS_ORIGINS": test_origins,
            "SECRET_KEY": "a-secure-secret-key-with-sufficient-length-123456",
        },
    ):
        settings = Settings()
        # Verify explicit origins are preserved
        assert "https://home.example.com" in settings.CORS_ORIGINS
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        # Verify wildcard is not present
        assert "*" not in settings.CORS_ORIGINS


def test_cors_default_origins_when_not_set():
    """When CORS_ORIGINS env var is not set, use safe localhost defaults."""
    with patch.dict(
        os.environ, {"SECRET_KEY": "a-secure-secret-key-with-sufficient-length-123456"}, clear=False
    ):
        # Ensure CORS_ORIGINS is not in environment
        if "CORS_ORIGINS" in os.environ:
            del os.environ["CORS_ORIGINS"]
        settings = Settings()
        # Verify default localhost origins are used
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS
        # Verify wildcard is not present
        assert "*" not in settings.CORS_ORIGINS
