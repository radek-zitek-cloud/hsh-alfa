"""
Shared HTTP client service with retry logic and SSRF protection.

This module provides a centralized HTTP client for making external API requests
across all widgets and services, reducing code duplication and ensuring consistent
security policies and error handling.
"""
import logging
import aiohttp
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import ipaddress
import socket

logger = logging.getLogger(__name__)

# Default timeout for HTTP requests (in seconds)
DEFAULT_TIMEOUT = 10

# Maximum content size to fetch (10MB)
MAX_CONTENT_SIZE = 10 * 1024 * 1024

# Private IP ranges and special addresses to block (SSRF protection)
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('10.0.0.0/8'),       # Private
    ipaddress.ip_network('172.16.0.0/12'),    # Private
    ipaddress.ip_network('192.168.0.0/16'),   # Private
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local (AWS metadata)
    ipaddress.ip_network('::1/128'),          # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),         # IPv6 private
    ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
]

# Default user agent
DEFAULT_USER_AGENT = 'Mozilla/5.0 (compatible; HSH-Alfa/1.0)'


def is_safe_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF (Server-Side Request Forgery) attacks.

    Checks that the URL uses http/https scheme and doesn't target private
    or internal IP addresses.

    Args:
        url: The URL to validate

    Returns:
        True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)

        # Only allow http/https schemes
        if parsed.scheme not in ['http', 'https']:
            logger.warning(f"Blocked non-http(s) URL: {url}")
            return False

        # Block localhost
        if parsed.hostname in ['localhost', '0.0.0.0']:
            logger.warning(f"Blocked localhost URL: {url}")
            return False

        # Try to resolve hostname to IP and check against blocked ranges
        if parsed.hostname:
            try:
                # Get IP addresses for the hostname
                addr_info = socket.getaddrinfo(parsed.hostname, None)
                for addr in addr_info:
                    ip = ipaddress.ip_address(addr[4][0])
                    for blocked_range in BLOCKED_IP_RANGES:
                        if ip in blocked_range:
                            logger.warning(f"Blocked private/internal IP URL: {url} ({ip})")
                            return False
            except (socket.gaierror, ValueError) as e:
                logger.debug(f"Could not resolve hostname {parsed.hostname}: {e}")
                # If we can't resolve, block it to be safe
                return False

        return True
    except Exception as e:
        logger.warning(f"Error validating URL {url}: {e}")
        return False


class HttpClient:
    """
    Shared HTTP client for making external API requests.

    Provides consistent timeout, retry logic, security checks (SSRF protection),
    and error handling across all external HTTP requests.
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        verify_ssl: bool = True
    ):
        """
        Initialize HTTP client with configuration.

        Args:
            timeout: Request timeout in seconds
            user_agent: User-Agent header value
            verify_ssl: Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            'User-Agent': self.user_agent
        }

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True
    ) -> aiohttp.ClientResponse:
        """
        Make a GET request.

        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)

        Returns:
            aiohttp.ClientResponse object

        Raises:
            ValueError: If URL fails SSRF validation
            aiohttp.ClientError: If request fails
        """
        if validate_url and not is_safe_url(url):
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        async with aiohttp.ClientSession(
            timeout=timeout_obj,
            headers=request_headers
        ) as session:
            async with session.get(
                url,
                params=params,
                allow_redirects=True,
                ssl=self.verify_ssl
            ) as response:
                # Check response status
                response.raise_for_status()
                return response

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True
    ) -> Dict[str, Any]:
        """
        Make a GET request and return JSON response.

        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)

        Returns:
            Dictionary containing JSON response

        Raises:
            ValueError: If URL fails SSRF validation
            aiohttp.ClientError: If request fails
            ValueError: If response is not valid JSON
        """
        if validate_url and not is_safe_url(url):
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        async with aiohttp.ClientSession(
            timeout=timeout_obj,
            headers=request_headers
        ) as session:
            async with session.get(
                url,
                params=params,
                allow_redirects=True,
                ssl=self.verify_ssl
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True,
        max_size: int = MAX_CONTENT_SIZE
    ) -> str:
        """
        Make a GET request and return text response.

        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)
            max_size: Maximum content size in bytes

        Returns:
            String containing response text

        Raises:
            ValueError: If URL fails SSRF validation or content too large
            aiohttp.ClientError: If request fails
        """
        if validate_url and not is_safe_url(url):
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        async with aiohttp.ClientSession(
            timeout=timeout_obj,
            headers=request_headers
        ) as session:
            async with session.get(
                url,
                params=params,
                allow_redirects=True,
                ssl=self.verify_ssl
            ) as response:
                response.raise_for_status()

                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_size:
                    raise ValueError(f"Content too large ({content_length} bytes), max {max_size}")

                text = await response.text()

                # Check actual size
                if len(text) > max_size:
                    raise ValueError(f"Content too large ({len(text)} bytes), max {max_size}")

                return text

    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True
    ) -> aiohttp.ClientResponse:
        """
        Make a HEAD request.

        Args:
            url: The URL to check
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)

        Returns:
            aiohttp.ClientResponse object

        Raises:
            ValueError: If URL fails SSRF validation
            aiohttp.ClientError: If request fails
        """
        if validate_url and not is_safe_url(url):
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        async with aiohttp.ClientSession(
            timeout=timeout_obj,
            headers=request_headers
        ) as session:
            async with session.head(
                url,
                allow_redirects=True,
                ssl=self.verify_ssl
            ) as response:
                response.raise_for_status()
                return response


# Global HTTP client instance for convenience
http_client = HttpClient()
