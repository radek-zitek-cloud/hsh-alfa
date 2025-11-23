"""Favicon fetching service."""
import logging
import ipaddress
from urllib.parse import urljoin, urlparse
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Maximum HTML size to fetch (5MB)
MAX_HTML_SIZE = 5 * 1024 * 1024

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


def is_safe_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.

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
                import socket
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


async def validate_favicon_url(favicon_url: str, timeout: int = 5) -> bool:
    """
    Validate that a favicon URL is accessible.

    Args:
        favicon_url: The favicon URL to validate
        timeout: Request timeout in seconds

    Returns:
        True if favicon is accessible, False otherwise
    """
    if not is_safe_url(favicon_url):
        return False

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(favicon_url, allow_redirects=True) as response:
                return response.status == 200
    except Exception as e:
        logger.debug(f"Failed to validate favicon URL {favicon_url}: {e}")
        return False


async def fetch_favicon(url: str, timeout: int = 10) -> Optional[str]:
    """
    Attempt to fetch favicon URL for a given website URL.

    Tries multiple strategies:
    1. Common favicon locations (/favicon.ico, /apple-touch-icon.png)
    2. Parse HTML for favicon link tags
    3. Google's favicon service as fallback

    Args:
        url: The website URL to fetch favicon for
        timeout: Request timeout in seconds

    Returns:
        Favicon URL if found, None otherwise
    """
    try:
        # Validate URL for SSRF protection
        if not is_safe_url(url):
            logger.warning(f"Blocked unsafe URL: {url}")
            return None

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"Invalid URL format: {url}")
            return None

        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Set User-Agent header to avoid being blocked by some servers
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; FaviconFetcher/1.0)'
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout),
            headers=headers
        ) as session:
            # Strategy 1: Try common favicon locations
            common_paths = [
                "/favicon.ico",
                "/favicon.png",
                "/apple-touch-icon.png",
                "/apple-touch-icon-precomposed.png"
            ]

            for path in common_paths:
                favicon_url = urljoin(base_url, path)

                # Validate each constructed URL
                if not is_safe_url(favicon_url):
                    continue

                try:
                    async with session.head(favicon_url, allow_redirects=True) as response:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            if 'image' in content_type or path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                                logger.info(f"Found favicon at common location: {favicon_url}")
                                return favicon_url
                except Exception as e:
                    logger.debug(f"Failed to fetch {favicon_url}: {e}")
                    continue

            # Strategy 2: Parse HTML for favicon link tags
            try:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        # Check Content-Length header to prevent downloading huge files
                        content_length = response.headers.get('Content-Length')
                        if content_length and int(content_length) > MAX_HTML_SIZE:
                            logger.warning(f"HTML content too large ({content_length} bytes), skipping HTML parsing")
                        else:
                            # Read with size limit
                            html = await response.text()
                            if len(html) > MAX_HTML_SIZE:
                                logger.warning(f"HTML content too large ({len(html)} bytes), skipping HTML parsing")
                            else:
                                # Specify HTML parser explicitly for better performance and security
                                soup = BeautifulSoup(html, 'html.parser')

                                # Look for favicon link tags with multi-value rel attribute support
                                # Using a lambda to check if 'icon' is in the space-separated rel values
                                link = soup.find('link', rel=lambda x: x and 'icon' in x.split())

                                if link and link.get('href'):
                                    favicon_url = urljoin(base_url, link['href'])

                                    # Validate the constructed URL
                                    if is_safe_url(favicon_url):
                                        logger.info(f"Found favicon in HTML: {favicon_url}")
                                        return favicon_url

            except Exception as e:
                logger.debug(f"Failed to parse HTML for favicon: {e}")

            # Strategy 3: Use Google's favicon service as fallback
            google_favicon_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64"

            # Validate that Google's service actually returns a valid favicon
            if await validate_favicon_url(google_favicon_url, timeout=timeout):
                logger.info(f"Using Google favicon service as fallback: {google_favicon_url}")
                return google_favicon_url
            else:
                logger.info(f"Google favicon service did not return a valid favicon for: {parsed.netloc}")
                return None

    except Exception as e:
        logger.error(f"Error fetching favicon for {url}: {e}")
        return None
