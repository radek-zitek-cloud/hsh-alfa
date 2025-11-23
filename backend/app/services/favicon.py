"""Favicon fetching service."""
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"Invalid URL format: {url}")
            return None

        base_url = f"{parsed.scheme}://{parsed.netloc}"

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # Strategy 1: Try common favicon locations
            common_paths = [
                "/favicon.ico",
                "/favicon.png",
                "/apple-touch-icon.png",
                "/apple-touch-icon-precomposed.png"
            ]

            for path in common_paths:
                favicon_url = urljoin(base_url, path)
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
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Look for various favicon link tags
                        favicon_selectors = [
                            {'rel': 'icon'},
                            {'rel': 'shortcut icon'},
                            {'rel': 'apple-touch-icon'},
                            {'rel': 'apple-touch-icon-precomposed'}
                        ]

                        for selector in favicon_selectors:
                            link = soup.find('link', attrs=selector)
                            if link and link.get('href'):
                                favicon_url = urljoin(base_url, link['href'])
                                logger.info(f"Found favicon in HTML: {favicon_url}")
                                return favicon_url

            except Exception as e:
                logger.debug(f"Failed to parse HTML for favicon: {e}")

            # Strategy 3: Use Google's favicon service as fallback
            google_favicon_url = f"https://www.google.com/s2/favicons?domain={parsed.netloc}&sz=64"
            logger.info(f"Using Google favicon service as fallback: {google_favicon_url}")
            return google_favicon_url

    except Exception as e:
        logger.error(f"Error fetching favicon for {url}: {e}")
        return None


async def validate_favicon_url(favicon_url: str, timeout: int = 5) -> bool:
    """
    Validate that a favicon URL is accessible.

    Args:
        favicon_url: The favicon URL to validate
        timeout: Request timeout in seconds

    Returns:
        True if favicon is accessible, False otherwise
    """
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.head(favicon_url, allow_redirects=True) as response:
                return response.status == 200
    except Exception as e:
        logger.debug(f"Failed to validate favicon URL {favicon_url}: {e}")
        return False
