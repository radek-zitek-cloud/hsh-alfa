"""Logging utilities for sanitizing sensitive data."""
import re
from typing import Any, Dict


# Patterns that indicate sensitive data
SENSITIVE_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'auth',
    r'credential',
    r'private[_-]?key',
    r'access[_-]?key',
    r'bearer',
]


def is_sensitive_key(key: str) -> bool:
    """
    Check if a key name indicates it contains sensitive data.

    Args:
        key: The key name to check

    Returns:
        True if the key name matches a sensitive pattern
    """
    key_lower = key.lower()
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, key_lower):
            return True
    return False


def sanitize_log_value(key: str, value: Any, max_length: int = 50) -> str:
    """
    Sanitize a value for safe logging.

    Args:
        key: The key name (used to detect sensitive data)
        value: The value to sanitize
        max_length: Maximum length for non-sensitive values (default: 50)

    Returns:
        Sanitized string safe for logging
    """
    # Convert value to string
    if not isinstance(value, str):
        value = str(value)

    # Redact sensitive values
    if is_sensitive_key(key):
        return "[REDACTED]"

    # Truncate long values
    if len(value) > max_length:
        return value[:max_length] + "..."

    return value


def sanitize_log_dict(data: Dict[str, Any], max_length: int = 50) -> Dict[str, str]:
    """
    Sanitize a dictionary for safe logging.

    Args:
        data: Dictionary to sanitize
        max_length: Maximum length for non-sensitive values (default: 50)

    Returns:
        Dictionary with sanitized values
    """
    sanitized = {}
    for key, value in data.items():
        sanitized[key] = sanitize_log_value(key, value, max_length)
    return sanitized
