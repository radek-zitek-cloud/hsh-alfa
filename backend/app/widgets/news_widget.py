"""News/RSS widget implementation."""
import feedparser
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.widgets.base_widget import BaseWidget
from app.config import settings
from app.logging_config import get_logger
from app.services.http_client import http_client

logger = get_logger(__name__)


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
                logger.warning(
                    "News API key not configured",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id
                    }
                )
                return False

        # Must have at least one news source
        if not has_rss_feeds and not has_news_api:
            logger.warning(
                "No news sources configured (rss_feeds or use_news_api)",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id
                }
            )
            return False

        logger.debug(
            "News widget configuration validated",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "has_rss_feeds": has_rss_feeds,
                "has_news_api": has_news_api,
                "num_rss_feeds": len(self.config.get("rss_feeds", []))
            }
        )
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

        logger.info(
            "Fetching articles from RSS feeds",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "num_feeds": len(feeds)
            }
        )

        for feed_url in feeds:
            try:
                logger.debug(
                    "Fetching RSS feed",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "api_url": feed_url
                    }
                )

                # Use SSRF-protected HTTP client to fetch RSS feed
                content = await http_client.get_text(
                    feed_url,
                    timeout=10,
                    validate_url=True
                )

                # Parse RSS feed (feedparser is sync, but fast)
                feed = feedparser.parse(content)

                logger.debug(
                    "RSS feed parsed successfully",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "feed_title": feed.feed.get('title', 'Unknown'),
                        "num_entries": len(feed.entries),
                        "api_url": feed_url
                    }
                )

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
                        except Exception as e:
                            logger.debug("Failed to parse RSS entry published date", extra={
                                "operation": "rss_date_parsing",
                                "error_type": type(e).__name__,
                                "entry_title": entry.get('title', 'unknown')
                            })
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
                logger.error(
                    f"Error fetching RSS feed: {str(e)}",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "api_url": feed_url,
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                continue

        logger.info(
            "RSS feed fetch completed",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "total_articles": len(articles)
            }
        )

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
            logger.info(
                "Fetching news articles from News API (everything endpoint)",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "api_url": url,
                    "query": query,
                    "language": language
                }
            )
        else:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "category": category,
                "country": country,
                "apiKey": api_key,
                "pageSize": self.config.get("max_articles", 10)
            }
            logger.info(
                "Fetching news articles from News API (top-headlines endpoint)",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "api_url": url,
                    "category": category,
                    "country": country
                }
            )

        try:
            # Use SSRF-protected HTTP client to fetch from News API
            data = await http_client.get_json(
                url,
                params=params,
                timeout=10,
                validate_url=True
            )

            logger.debug(
                "News API response received",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "api_url": url
                }
            )

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

            logger.info(
                "News API articles retrieved successfully",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "num_articles": len(articles)
                }
            )

        except Exception as e:
            logger.error(
                f"Error fetching from News API: {str(e)}",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "api_url": url,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )

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
