"""Rate limiting configuration and utilities."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance that will be shared across the application
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
