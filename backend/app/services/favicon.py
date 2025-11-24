"""
Favicon fetching service.

This service handles automatic favicon discovery and fetching for websites,
using multiple strategies to find the best available favicon.
"""
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional
from bs4 import BeautifulSoup

from app.services.http_client import HttpClient, is_safe_url

logger = logging.getLogger(__name__)

# Maximum HTML size to fetch (5MB)
MAX_HTML_SIZE = 5 * 1024 * 1024


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
        client = HttpClient(timeout=timeout)
        response = await client.head(favicon_url)
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

        # Create HTTP client with custom user agent
        client = HttpClient(
            timeout=timeout,
            user_agent='Mozilla/5.0 (compatible; FaviconFetcher/1.0)'
        )

        # Strategy 1: Try common favicon locations
        favicon_url = await _try_common_locations(client, base_url)
        if favicon_url:
            return favicon_url

        # Strategy 2: Parse HTML for favicon link tags
        favicon_url = await _parse_html_for_favicon(client, url, base_url)
        if favicon_url:
            return favicon_url

        # Strategy 3: Use Google's favicon service as fallback
        return await _try_google_favicon_service(parsed.netloc, timeout)

    except Exception as e:
        logger.error(f"Error fetching favicon for {url}: {e}")
        return None


async def _try_common_locations(client: HttpClient, base_url: str) -> Optional[str]:
    """
    Try common favicon file locations.

    Args:
        client: HTTP client
        base_url: Base URL of the website

    Returns:
        Favicon URL if found, None otherwise
    """
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
            response = await client.head(favicon_url)
            if response.status == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type or path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    logger.info(f"Found favicon at common location: {favicon_url}")
                    return favicon_url
        except Exception as e:
            logger.debug(f"Failed to fetch {favicon_url}: {e}")
            continue

    return None


async def _parse_html_for_favicon(
    client: HttpClient,
    url: str,
    base_url: str
) -> Optional[str]:
    """
    Parse HTML to find favicon link tags.

    Args:
        client: HTTP client
        url: Full URL to fetch
        base_url: Base URL of the website

    Returns:
        Favicon URL if found, None otherwise
    """
    try:
        html = await client.get_text(url, max_size=MAX_HTML_SIZE)

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

    except ValueError as e:
        # Catch size limit errors
        logger.warning(f"HTML parsing failed: {e}")
    except Exception as e:
        logger.debug(f"Failed to parse HTML for favicon: {e}")

    return None


async def _try_google_favicon_service(domain: str, timeout: int) -> Optional[str]:
    """
    Try Google's favicon service as a fallback.

    Args:
        domain: Domain name
        timeout: Request timeout

    Returns:
        Google favicon URL if valid, None otherwise
    """
    google_favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

    # Validate that Google's service actually returns a valid favicon
    if await validate_favicon_url(google_favicon_url, timeout=timeout):
        logger.info(f"Using Google favicon service as fallback: {google_favicon_url}")
        return google_favicon_url
    else:
        logger.info(f"Google favicon service did not return a valid favicon for: {domain}")
        return None
