"""Tests for security-related configuration validation."""
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
