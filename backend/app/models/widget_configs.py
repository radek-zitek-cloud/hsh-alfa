"""Widget-specific configuration schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class WeatherWidgetConfig(BaseModel):
    """Weather widget configuration schema."""
    location: str = Field(..., min_length=1, max_length=255, description="City name or location")
    units: str = Field(default="metric", pattern="^(metric|imperial|standard)$", description="Temperature units")
    show_forecast: bool = Field(default=True, description="Whether to show forecast")
    api_key: Optional[str] = Field(None, min_length=10, max_length=255, description="OpenWeatherMap API key (optional)")

    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate location is not empty after stripping."""
        if not v.strip():
            raise ValueError('Location cannot be empty or whitespace only')
        return v.strip()


class NewsWidgetConfig(BaseModel):
    """News widget configuration schema."""
    rss_feeds: List[str] = Field(default_factory=list, max_length=10, description="List of RSS feed URLs")
    use_news_api: bool = Field(default=False, description="Use News API instead of RSS feeds")
    api_key: Optional[str] = Field(None, min_length=10, max_length=255, description="News API key (optional)")
    max_articles: int = Field(default=10, ge=1, le=50, description="Maximum number of articles to display")
    query: Optional[str] = Field(None, max_length=100, description="Search query for News API")
    category: str = Field(default="general", max_length=50, description="News category for News API")
    country: str = Field(default="us", pattern="^[a-z]{2}$", description="Country code (ISO 3166-1 alpha-2)")
    language: str = Field(default="en", pattern="^[a-z]{2}$", description="Language code (ISO 639-1)")
    description_length: int = Field(default=200, ge=50, le=500, description="Maximum description length")

    @field_validator('rss_feeds')
    @classmethod
    def validate_rss_urls(cls, v: List[str]) -> List[str]:
        """Validate RSS feed URLs."""
        if not v:
            return v

        validated_feeds = []
        for url in v:
            url = url.strip()
            if not url:
                continue
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'RSS feed URLs must start with http:// or https://: {url}')
            if len(url) > 2048:
                raise ValueError(f'RSS feed URL too long (max 2048 characters): {url[:50]}...')
            validated_feeds.append(url)

        return validated_feeds

    def model_post_init(self, __context) -> None:
        """Validate that at least one news source is configured."""
        if not self.rss_feeds and not self.use_news_api:
            raise ValueError('At least one of rss_feeds or use_news_api must be configured')


class ExchangeRateWidgetConfig(BaseModel):
    """Exchange rate widget configuration schema."""
    base_currency: str = Field(..., min_length=3, max_length=3, pattern="^[A-Z]{3}$", description="Base currency code (ISO 4217)")
    target_currencies: List[str] = Field(..., min_length=1, max_length=20, description="List of target currency codes")
    show_trend: bool = Field(default=False, description="Show trend indicators")
    api_key: Optional[str] = Field(None, min_length=10, max_length=255, description="Exchange rate API key (optional)")

    @field_validator('base_currency')
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        """Validate and normalize base currency."""
        return v.upper().strip()

    @field_validator('target_currencies')
    @classmethod
    def validate_target_currencies(cls, v: List[str]) -> List[str]:
        """Validate target currencies."""
        if not v:
            raise ValueError('At least one target currency must be specified')

        validated_currencies = []
        for currency in v:
            currency = currency.strip().upper()
            if not currency:
                continue
            if len(currency) != 3:
                raise ValueError(f'Currency code must be 3 characters: {currency}')
            if not currency.isalpha():
                raise ValueError(f'Currency code must contain only letters: {currency}')
            validated_currencies.append(currency)

        if not validated_currencies:
            raise ValueError('At least one valid target currency must be specified')

        return validated_currencies


class MarketWidgetConfig(BaseModel):
    """Market widget configuration schema."""
    stocks: List[str] = Field(default_factory=list, max_length=20, description="List of stock symbols")
    crypto: List[str] = Field(default_factory=list, max_length=20, description="List of crypto symbols")

    @field_validator('stocks')
    @classmethod
    def validate_stocks(cls, v: List[str]) -> List[str]:
        """Validate stock symbols."""
        if not v:
            return v

        validated_stocks = []
        for symbol in v:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            if len(symbol) > 10:
                raise ValueError(f'Stock symbol too long (max 10 characters): {symbol}')
            # Allow letters, numbers, dots, and caret (for indices like ^GSPC)
            if not all(c.isalnum() or c in '.^-' for c in symbol):
                raise ValueError(f'Stock symbol contains invalid characters: {symbol}')
            validated_stocks.append(symbol)

        return validated_stocks

    @field_validator('crypto')
    @classmethod
    def validate_crypto(cls, v: List[str]) -> List[str]:
        """Validate crypto symbols."""
        if not v:
            return v

        validated_crypto = []
        for symbol in v:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            if len(symbol) > 10:
                raise ValueError(f'Crypto symbol too long (max 10 characters): {symbol}')
            if not symbol.replace('-', '').isalnum():
                raise ValueError(f'Crypto symbol contains invalid characters: {symbol}')
            validated_crypto.append(symbol)

        return validated_crypto

    def model_post_init(self, __context) -> None:
        """Validate that at least one market type is configured."""
        if not self.stocks and not self.crypto:
            raise ValueError('At least one of stocks or crypto must be configured')


# Map widget types to their configuration schemas
WIDGET_CONFIG_SCHEMAS = {
    'weather': WeatherWidgetConfig,
    'news': NewsWidgetConfig,
    'exchange_rate': ExchangeRateWidgetConfig,
    'market': MarketWidgetConfig,
}


def validate_widget_config(widget_type: str, config: dict) -> dict:
    """
    Validate widget configuration based on widget type.

    Args:
        widget_type: Type of widget
        config: Configuration dictionary

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If widget type is unknown or configuration is invalid
    """
    if widget_type not in WIDGET_CONFIG_SCHEMAS:
        raise ValueError(f"Unknown widget type: {widget_type}. Allowed types: {', '.join(WIDGET_CONFIG_SCHEMAS.keys())}")

    schema_class = WIDGET_CONFIG_SCHEMAS[widget_type]
    validated_config = schema_class(**config)
    return validated_config.model_dump()
