"""
Shared HTTP client service with retry logic and SSRF protection.

This module provides a centralized HTTP client for making external API requests
across all widgets and services, reducing code duplication and ensuring consistent
security policies and error handling.
"""

import ipaddress
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

from app.logging_config import get_logger

logger = get_logger(__name__)

# Default timeout for HTTP requests (in seconds)
DEFAULT_TIMEOUT = 10

# Maximum content size to fetch (10MB)
MAX_CONTENT_SIZE = 10 * 1024 * 1024

# Private IP ranges and special addresses to block (SSRF protection)
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # Private
    ipaddress.ip_network("172.16.0.0/12"),  # Private
    ipaddress.ip_network("192.168.0.0/16"),  # Private
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local (AWS metadata)
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

# Default user agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; HSH-Alfa/1.0)"


class BlockedIPError(ValueError):
    """
    Exception raised when a connection to a blocked IP address is attempted.

    This exception is used to distinguish IP blocking from other ValueError exceptions
    during connection establishment.
    """

    pass


def is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """
    Check if an IP address is in the blocked ranges.

    Args:
        ip: IP address to check

    Returns:
        True if IP is blocked, False otherwise
    """
    for blocked_range in BLOCKED_IP_RANGES:
        if ip in blocked_range:
            return True
    return False


class SafeTCPConnector(aiohttp.TCPConnector):
    """
    Custom TCP connector that validates IPs at connection time to prevent DNS rebinding attacks.

    This connector resolves hostnames and checks each resolved IP against blocked ranges
    immediately before establishing the connection, preventing DNS rebinding attacks where
    DNS resolution could change between initial validation and actual connection.
    """

    async def _resolve_host(
        self, host: str, port: int, traces: Optional[List] = None
    ) -> List[Dict[str, Any]]:
        """
        Resolve host and validate IPs are not in blocked ranges.

        Args:
            host: Hostname to resolve
            port: Port number
            traces: Optional traces for monitoring

        Returns:
            List of resolved address info dicts

        Raises:
            BlockedIPError: If any resolved IP is in blocked ranges
        """
        # Resolve using parent class
        resolved = await super()._resolve_host(host, port, traces)

        # Validate each resolved IP
        for addr_info in resolved:
            ip_str = addr_info["host"]
            try:
                ip = ipaddress.ip_address(ip_str)
                if is_blocked_ip(ip):
                    logger.warning(
                        "Blocked connection to private/internal IP",
                        extra={
                            "operation": "ssrf_validation",
                            "reason": "private_ip_blocked_at_connection",
                            "hostname": host,
                            "ip": str(ip),
                        },
                    )
                    raise BlockedIPError(f"Connection to private/internal IP blocked: {ip}")
            except BlockedIPError:
                # Re-raise blocked IP errors
                raise
            except ValueError:
                # If IP parsing fails, block it
                logger.warning(
                    "Could not parse resolved IP",
                    extra={"operation": "ssrf_validation", "hostname": host, "ip_str": ip_str},
                )
                raise BlockedIPError(f"Invalid IP address resolved: {ip_str}")

        return resolved


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
        if parsed.scheme not in ["http", "https"]:
            logger.warning(
                "Blocked non-http(s) URL",
                extra={
                    "operation": "ssrf_validation",
                    "reason": "invalid_scheme",
                    "scheme": parsed.scheme,
                },
            )
            return False

        # Block localhost
        if parsed.hostname in ["localhost", "0.0.0.0"]:
            logger.warning(
                "Blocked localhost URL",
                extra={
                    "operation": "ssrf_validation",
                    "reason": "localhost_blocked",
                    "hostname": parsed.hostname,
                },
            )
            return False

        # Try to resolve hostname to IP and check against blocked ranges
        if parsed.hostname:
            try:
                # Get IP addresses for the hostname
                addr_info = socket.getaddrinfo(parsed.hostname, None)
                for addr in addr_info:
                    ip = ipaddress.ip_address(addr[4][0])
                    if is_blocked_ip(ip):
                        logger.warning(
                            "Blocked private/internal IP URL",
                            extra={
                                "operation": "ssrf_validation",
                                "reason": "private_ip_blocked",
                                "hostname": parsed.hostname,
                                "ip": str(ip),
                            },
                        )
                        return False
            except (socket.gaierror, ValueError) as e:
                logger.debug(
                    "Could not resolve hostname",
                    extra={
                        "operation": "ssrf_validation",
                        "hostname": parsed.hostname,
                        "error_type": type(e).__name__,
                    },
                )
                # If we can't resolve, block it to be safe
                return False

        return True
    except Exception as e:
        logger.warning(
            "Error validating URL",
            extra={
                "operation": "ssrf_validation",
                "reason": "validation_error",
                "error_type": type(e).__name__,
            },
        )
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
        verify_ssl: bool = True,
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
        # Create connector once for connection pooling
        self.connector = SafeTCPConnector(ssl=self.verify_ssl)

    async def close(self):
        """Close the connector and cleanup resources."""
        if self.connector:
            await self.connector.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {"User-Agent": self.user_agent}

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True,
    ) -> bytes:
        """
        Make a GET request and return response body.

        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)

        Returns:
            Response body as bytes

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

        # Use SafeTCPConnector to prevent DNS rebinding attacks
        async with aiohttp.ClientSession(
            timeout=timeout_obj, headers=request_headers, connector=self.connector
        ) as session:
            async with session.get(url, params=params, allow_redirects=True) as response:
                # Check response status
                response.raise_for_status()
                # Read response body before context exits
                return await response.read()

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True,
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
            logger.warning(
                "Unsafe URL blocked for JSON request",
                extra={"operation": "http_request_blocked", "request_type": "json"},
            )
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        try:
            logger.debug(
                "Making JSON HTTP request",
                extra={
                    "operation": "http_request",
                    "request_type": "json",
                    "timeout": request_timeout,
                },
            )
            # Use SafeTCPConnector to prevent DNS rebinding attacks
            async with aiohttp.ClientSession(
                timeout=timeout_obj, headers=request_headers, connector=self.connector
            ) as session:
                async with session.get(url, params=params, allow_redirects=True) as response:
                    response.raise_for_status()
                    logger.debug(
                        "JSON response received successfully",
                        extra={"operation": "http_request_success", "status_code": response.status},
                    )
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(
                "HTTP request failed",
                extra={
                    "operation": "http_request_failed",
                    "request_type": "json",
                    "error_type": type(e).__name__,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during JSON request",
                extra={"operation": "http_request_error", "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    async def get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True,
        max_size: int = MAX_CONTENT_SIZE,
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
            logger.warning(
                "Unsafe URL blocked for text request",
                extra={"operation": "http_request_blocked", "request_type": "text"},
            )
            raise ValueError(f"Unsafe URL blocked: {url}")

        # Merge headers
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # Use custom timeout if provided
        request_timeout = timeout if timeout is not None else self.timeout

        timeout_obj = aiohttp.ClientTimeout(total=request_timeout)

        try:
            logger.debug(
                "Making text HTTP request",
                extra={
                    "operation": "http_request",
                    "request_type": "text",
                    "timeout": request_timeout,
                    "max_size": max_size,
                },
            )
            # Use SafeTCPConnector to prevent DNS rebinding attacks
            async with aiohttp.ClientSession(
                timeout=timeout_obj, headers=request_headers, connector=self.connector
            ) as session:
                async with session.get(url, params=params, allow_redirects=True) as response:
                    response.raise_for_status()

                    # Check content length
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_size:
                        logger.warning(
                            "Content size exceeds maximum",
                            extra={
                                "operation": "http_request_failed",
                                "request_type": "text",
                                "reason": "content_too_large",
                                "content_length": int(content_length),
                                "max_size": max_size,
                            },
                        )
                        raise ValueError(
                            f"Content too large ({content_length} bytes), max {max_size}"
                        )

                    text = await response.text()

                    # Check actual size
                    if len(text) > max_size:
                        logger.warning(
                            "Actual content size exceeds maximum",
                            extra={
                                "operation": "http_request_failed",
                                "request_type": "text",
                                "reason": "content_too_large",
                                "content_length": len(text),
                                "max_size": max_size,
                            },
                        )
                        raise ValueError(f"Content too large ({len(text)} bytes), max {max_size}")

                    logger.debug(
                        "Text response received successfully",
                        extra={
                            "operation": "http_request_success",
                            "status_code": response.status,
                            "content_length": len(text),
                        },
                    )
                    return text
        except aiohttp.ClientError as e:
            logger.error(
                "HTTP request failed",
                extra={
                    "operation": "http_request_failed",
                    "request_type": "text",
                    "error_type": type(e).__name__,
                },
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during text request",
                extra={"operation": "http_request_error", "error_type": type(e).__name__},
                exc_info=True,
            )
            raise

    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        validate_url: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a HEAD request and return status and headers.

        Args:
            url: The URL to check
            headers: Optional custom headers (merged with defaults)
            timeout: Optional custom timeout (overrides instance timeout)
            validate_url: Whether to validate URL for SSRF protection (default: True)

        Returns:
            Dictionary with 'status' and 'headers' keys

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

        # Use SafeTCPConnector to prevent DNS rebinding attacks
        async with aiohttp.ClientSession(
            timeout=timeout_obj, headers=request_headers, connector=self.connector
        ) as session:
            async with session.head(url, allow_redirects=True) as response:
                response.raise_for_status()
                # Extract status and headers before context exits
                return {"status": response.status, "headers": dict(response.headers)}


# Global HTTP client instance for convenience
http_client = HttpClient()
