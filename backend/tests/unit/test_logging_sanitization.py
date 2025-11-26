"""Unit tests for logging sanitization utilities."""

import pytest

from app.utils.logging import is_sensitive_key, sanitize_log_dict, sanitize_log_value


class TestIsSensitiveKey:
    """Tests for is_sensitive_key function."""

    def test_detects_api_key(self):
        """Test detection of api_key pattern."""
        assert is_sensitive_key("api_key")
        assert is_sensitive_key("API_KEY")
        assert is_sensitive_key("weather_api_key")
        assert is_sensitive_key("apiKey")
        assert is_sensitive_key("api-key")

    def test_detects_password(self):
        """Test detection of password pattern."""
        assert is_sensitive_key("password")
        assert is_sensitive_key("PASSWORD")
        assert is_sensitive_key("user_password")
        assert is_sensitive_key("db_password")

    def test_detects_secret(self):
        """Test detection of secret pattern."""
        assert is_sensitive_key("secret")
        assert is_sensitive_key("SECRET")
        assert is_sensitive_key("client_secret")
        assert is_sensitive_key("SECRET_KEY")

    def test_detects_token(self):
        """Test detection of token pattern."""
        assert is_sensitive_key("token")
        assert is_sensitive_key("TOKEN")
        assert is_sensitive_key("access_token")
        assert is_sensitive_key("refresh_token")
        assert is_sensitive_key("bearer_token")

    def test_detects_auth(self):
        """Test detection of auth pattern."""
        assert is_sensitive_key("auth")
        assert is_sensitive_key("AUTH")
        assert is_sensitive_key("authorization")
        assert is_sensitive_key("auth_header")

    def test_detects_credential(self):
        """Test detection of credential pattern."""
        assert is_sensitive_key("credential")
        assert is_sensitive_key("credentials")
        assert is_sensitive_key("user_credentials")

    def test_detects_private_key(self):
        """Test detection of private_key pattern."""
        assert is_sensitive_key("private_key")
        assert is_sensitive_key("PRIVATE_KEY")
        assert is_sensitive_key("ssh_private_key")

    def test_does_not_detect_safe_keys(self):
        """Test that safe keys are not flagged as sensitive."""
        assert not is_sensitive_key("location")
        assert not is_sensitive_key("username")
        assert not is_sensitive_key("email")
        assert not is_sensitive_key("description")
        assert not is_sensitive_key("title")
        assert not is_sensitive_key("id")


class TestSanitizeLogValue:
    """Tests for sanitize_log_value function."""

    def test_redacts_api_key(self):
        """Test that api_key values are redacted."""
        result = sanitize_log_value("api_key", "sk-1234567890abcdef")
        assert result == "[REDACTED]"

    def test_redacts_password(self):
        """Test that password values are redacted."""
        result = sanitize_log_value("password", "super_secret_password")
        assert result == "[REDACTED]"

    def test_redacts_secret(self):
        """Test that secret values are redacted."""
        result = sanitize_log_value("secret", "my_secret_value")
        assert result == "[REDACTED]"

    def test_redacts_token(self):
        """Test that token values are redacted."""
        result = sanitize_log_value("access_token", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        assert result == "[REDACTED]"

    def test_preserves_safe_short_values(self):
        """Test that safe short values are preserved."""
        result = sanitize_log_value("location", "Prague")
        assert result == "Prague"

        result = sanitize_log_value("username", "john_doe")
        assert result == "john_doe"

    def test_truncates_long_safe_values(self):
        """Test that long safe values are truncated."""
        long_value = "A" * 100
        result = sanitize_log_value("description", long_value, max_length=50)
        assert result == "A" * 50 + "..."
        assert len(result) == 53

    def test_handles_non_string_values(self):
        """Test that non-string values are converted to strings."""
        result = sanitize_log_value("count", 42)
        assert result == "42"

        result = sanitize_log_value("enabled", True)
        assert result == "True"

        result = sanitize_log_value("items", ["a", "b", "c"])
        assert "a" in result and "b" in result and "c" in result

    def test_custom_max_length(self):
        """Test custom max_length parameter."""
        result = sanitize_log_value("text", "Hello World!", max_length=5)
        assert result == "Hello..."

    def test_redacts_regardless_of_value_content(self):
        """Test that sensitive keys are redacted regardless of value content."""
        result = sanitize_log_value("api_key", "")
        assert result == "[REDACTED]"

        result = sanitize_log_value("password", "short")
        assert result == "[REDACTED]"


class TestSanitizeLogDict:
    """Tests for sanitize_log_dict function."""

    def test_sanitizes_dictionary_with_mixed_keys(self):
        """Test sanitizing dictionary with both sensitive and safe keys."""
        data = {
            "location": "Prague",
            "api_key": "sk-1234567890",
            "username": "john_doe",
            "password": "secret123",
        }
        result = sanitize_log_dict(data)

        assert result["location"] == "Prague"
        assert result["username"] == "john_doe"
        assert result["api_key"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"

    def test_sanitizes_empty_dictionary(self):
        """Test sanitizing empty dictionary."""
        result = sanitize_log_dict({})
        assert result == {}

    def test_truncates_long_values_in_dictionary(self):
        """Test that long values in dictionary are truncated."""
        data = {"description": "A" * 100, "title": "Short title"}
        result = sanitize_log_dict(data, max_length=50)

        assert result["description"] == "A" * 50 + "..."
        assert result["title"] == "Short title"

    def test_handles_nested_structures_as_strings(self):
        """Test handling of nested structures (converted to strings)."""
        data = {"config": {"nested": "value"}, "items": [1, 2, 3]}
        result = sanitize_log_dict(data)

        # Nested structures are converted to strings
        assert "nested" in result["config"]
        assert "1" in result["items"] or "[1, 2, 3]" in result["items"]

    def test_custom_max_length_in_dictionary(self):
        """Test custom max_length parameter for dictionary."""
        data = {"text1": "Hello World!", "text2": "Short"}
        result = sanitize_log_dict(data, max_length=5)

        assert result["text1"] == "Hello..."
        assert result["text2"] == "Short"

    def test_preserves_all_keys(self):
        """Test that all keys are preserved in result."""
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        result = sanitize_log_dict(data)

        assert set(result.keys()) == set(data.keys())
