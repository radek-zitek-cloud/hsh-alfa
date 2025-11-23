"""News/RSS widget implementation."""
import aiohttp
import feedparser
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.widgets.base_widget import BaseWidget
from app.config import settings

logger = logging.getLogger(__name__)


class NewsWidget(BaseWidget):
    """Widget for displaying news from RSS feeds or News API."""

    widget_type = "news"

    def validate_config(self) -> bool:
        """Validate news widget configuration."""
        # At least one of these must be configured
        has_rss_feeds = bool(self.config.get("rss_feeds"))
        has_news_api = bool(self.config.get("use_news_api"))

        # If using News API, check for API key
        if has_news_api:
            api_key = self.config.get("api_key") or settings.NEWS_API_KEY
            if not api_key:
                logger.error("News API key not configured")
                return False

        # Must have at least one news source
        if not has_rss_feeds and not has_news_api:
            logger.error("No news sources configured (rss_feeds or use_news_api)")
            return False

        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch news data from RSS feeds or News API.

        Returns:
            Dictionary containing news articles
        """
        articles = []

        # Fetch from RSS feeds if configured
        rss_feeds = self.config.get("rss_feeds", [])
        if rss_feeds:
            articles.extend(await self._fetch_rss_feeds(rss_feeds))

        # Fetch from News API if configured
        if self.config.get("use_news_api", False):
            api_articles = await self._fetch_news_api()
            articles.extend(api_articles)

        # Sort by published date (newest first)
        articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        # Limit number of articles
        max_articles = self.config.get("max_articles", 10)
        articles = articles[:max_articles]

        return self.transform_data(articles)

    async def _fetch_rss_feeds(self, feeds: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feeds.

        Args:
            feeds: List of RSS feed URLs

        Returns:
            List of articles
        """
        articles = []

        async with aiohttp.ClientSession() as session:
            for feed_url in feeds:
                try:
                    async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch RSS feed {feed_url}: {response.status}")
                            continue

                        content = await response.text()

                        # Parse RSS feed (feedparser is sync, but fast)
                        feed = feedparser.parse(content)

                        # Extract articles from feed
                        for entry in feed.entries:
                            # Get image from various possible fields
                            image_url = None
                            if hasattr(entry, 'media_content') and entry.media_content:
                                image_url = entry.media_content[0].get('url')
                            elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                                image_url = entry.media_thumbnail[0].get('url')
                            elif hasattr(entry, 'enclosures') and entry.enclosures:
                                for enclosure in entry.enclosures:
                                    if enclosure.get('type', '').startswith('image/'):
                                        image_url = enclosure.get('href')
                                        break

                            # Get description/summary
                            description = ""
                            if hasattr(entry, 'summary'):
                                description = entry.summary
                            elif hasattr(entry, 'description'):
                                description = entry.description

                            # Parse published date
                            published_at = ""
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    dt = datetime(*entry.published_parsed[:6])
                                    published_at = dt.isoformat() + "Z"
                                except Exception:
                                    pass
                            elif hasattr(entry, 'published'):
                                published_at = entry.published

                            article = {
                                "title": entry.get('title', 'No title'),
                                "description": description,
                                "url": entry.get('link', ''),
                                "image_url": image_url,
                                "published_at": published_at,
                                "source": feed.feed.get('title', 'RSS Feed')
                            }
                            articles.append(article)

                except Exception as e:
                    logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
                    continue

        return articles

    async def _fetch_news_api(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from News API.

        Returns:
            List of articles
        """
        api_key = self.config.get("api_key") or settings.NEWS_API_KEY
        query = self.config.get("query", "")
        category = self.config.get("category", "general")
        country = self.config.get("country", "us")
        language = self.config.get("language", "en")

        articles = []

        # Choose endpoint based on whether we have a query
        if query:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": language,
                "sortBy": "publishedAt",
                "apiKey": api_key,
                "pageSize": self.config.get("max_articles", 10)
            }
        else:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "category": category,
                "country": country,
                "apiKey": api_key,
                "pageSize": self.config.get("max_articles", 10)
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"News API error: {response.status} - {error_text}")
                        return articles

                    data = await response.json()

                    # Transform News API articles to common format
                    for item in data.get("articles", []):
                        article = {
                            "title": item.get("title", "No title"),
                            "description": item.get("description", ""),
                            "url": item.get("url", ""),
                            "image_url": item.get("urlToImage"),
                            "published_at": item.get("publishedAt", ""),
                            "source": item.get("source", {}).get("name", "News API")
                        }
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching from News API: {str(e)}")

        return articles

    def transform_data(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform articles to widget format.

        Args:
            articles: List of articles

        Returns:
            Transformed news data
        """
        # Clean up descriptions (remove HTML tags if present)
        for article in articles:
            if article.get("description"):
                # Simple HTML tag removal
                import re
                description = re.sub(r'<[^>]+>', '', article["description"])
                # Limit description length
                max_length = self.config.get("description_length", 200)
                if len(description) > max_length:
                    description = description[:max_length].rsplit(' ', 1)[0] + '...'
                article["description"] = description.strip()

        return {
            "articles": articles,
            "total": len(articles),
            "source_type": "rss" if self.config.get("rss_feeds") else "api"
        }
