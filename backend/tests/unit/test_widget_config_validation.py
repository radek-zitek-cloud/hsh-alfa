"""Unit tests for widget configuration validation."""
import pytest
from pydantic import ValidationError

from app.models.widget_configs import (
    WeatherWidgetConfig,
    NewsWidgetConfig,
    ExchangeRateWidgetConfig,
    MarketWidgetConfig,
    validate_widget_config,
)


class TestWeatherWidgetConfig:
    """Tests for WeatherWidgetConfig validation."""

    def test_valid_weather_config(self):
        """Test valid weather widget configuration."""
        config = WeatherWidgetConfig(
            location="Prague",
            units="metric",
            show_forecast=True
        )
        assert config.location == "Prague"
        assert config.units == "metric"
        assert config.show_forecast is True

    def test_weather_config_with_defaults(self):
        """Test weather config with default values."""
        config = WeatherWidgetConfig(location="London")
        assert config.location == "London"
        assert config.units == "metric"
        assert config.show_forecast is True
        assert config.api_key is None

    def test_weather_config_invalid_units(self):
        """Test weather config rejects invalid units."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherWidgetConfig(location="Prague", units="celsius")
        assert "units" in str(exc_info.value).lower()

    def test_weather_config_empty_location(self):
        """Test weather config rejects empty location."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherWidgetConfig(location="   ")
        assert "location" in str(exc_info.value).lower()

    def test_weather_config_missing_location(self):
        """Test weather config requires location."""
        with pytest.raises(ValidationError) as exc_info:
            WeatherWidgetConfig(units="metric")
        assert "location" in str(exc_info.value).lower()

    def test_weather_config_location_too_long(self):
        """Test weather config rejects location that's too long."""
        with pytest.raises(ValidationError):
            WeatherWidgetConfig(location="A" * 256)


class TestNewsWidgetConfig:
    """Tests for NewsWidgetConfig validation."""

    def test_valid_news_config_with_rss(self):
        """Test valid news widget config with RSS feeds."""
        config = NewsWidgetConfig(
            rss_feeds=["https://example.com/feed1.xml", "https://example.com/feed2.xml"],
            max_articles=10
        )
        assert len(config.rss_feeds) == 2
        assert config.max_articles == 10
        assert config.use_news_api is False

    def test_valid_news_config_with_news_api(self):
        """Test valid news widget config with News API."""
        config = NewsWidgetConfig(
            use_news_api=True,
            api_key="test-api-key-12345",
            query="technology"
        )
        assert config.use_news_api is True
        assert config.api_key == "test-api-key-12345"
        assert config.query == "technology"

    def test_news_config_no_sources(self):
        """Test news config requires at least one source."""
        with pytest.raises(ValueError) as exc_info:
            NewsWidgetConfig(use_news_api=False)
        assert "at least one" in str(exc_info.value).lower()

    def test_news_config_invalid_rss_url(self):
        """Test news config rejects invalid RSS URLs."""
        with pytest.raises(ValidationError) as exc_info:
            NewsWidgetConfig(rss_feeds=["ftp://invalid.com/feed.xml"])
        assert "http" in str(exc_info.value).lower()

    def test_news_config_filters_empty_rss_feeds(self):
        """Test news config filters out empty RSS feed URLs."""
        config = NewsWidgetConfig(
            rss_feeds=["https://example.com/feed.xml", "", "  "],
            use_news_api=False
        )
        assert len(config.rss_feeds) == 1
        assert config.rss_feeds[0] == "https://example.com/feed.xml"

    def test_news_config_max_articles_range(self):
        """Test news config validates max_articles range."""
        # Too low
        with pytest.raises(ValidationError):
            NewsWidgetConfig(rss_feeds=["https://example.com/feed.xml"], max_articles=0)

        # Too high
        with pytest.raises(ValidationError):
            NewsWidgetConfig(rss_feeds=["https://example.com/feed.xml"], max_articles=51)

        # Valid
        config = NewsWidgetConfig(rss_feeds=["https://example.com/feed.xml"], max_articles=25)
        assert config.max_articles == 25

    def test_news_config_too_many_rss_feeds(self):
        """Test news config limits number of RSS feeds."""
        with pytest.raises(ValidationError):
            NewsWidgetConfig(rss_feeds=[f"https://example{i}.com/feed.xml" for i in range(11)])

    def test_news_config_invalid_country_code(self):
        """Test news config validates country code."""
        with pytest.raises(ValidationError):
            NewsWidgetConfig(use_news_api=True, api_key="test-key", country="USA")


class TestExchangeRateWidgetConfig:
    """Tests for ExchangeRateWidgetConfig validation."""

    def test_valid_exchange_rate_config(self):
        """Test valid exchange rate widget configuration."""
        config = ExchangeRateWidgetConfig(
            base_currency="USD",
            target_currencies=["EUR", "GBP", "JPY"]
        )
        assert config.base_currency == "USD"
        assert len(config.target_currencies) == 3
        assert "EUR" in config.target_currencies

    def test_exchange_rate_normalizes_currency_codes(self):
        """Test exchange rate config normalizes currency codes to uppercase."""
        config = ExchangeRateWidgetConfig(
            base_currency="usd",
            target_currencies=["eur", "gbp"]
        )
        assert config.base_currency == "USD"
        assert config.target_currencies == ["EUR", "GBP"]

    def test_exchange_rate_missing_base_currency(self):
        """Test exchange rate config requires base currency."""
        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(target_currencies=["EUR"])

    def test_exchange_rate_missing_target_currencies(self):
        """Test exchange rate config requires target currencies."""
        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(base_currency="USD")

    def test_exchange_rate_empty_target_currencies(self):
        """Test exchange rate config rejects empty target currencies."""
        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(base_currency="USD", target_currencies=[])

    def test_exchange_rate_invalid_currency_length(self):
        """Test exchange rate config validates currency code length."""
        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(base_currency="US", target_currencies=["EUR"])

        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(base_currency="USD", target_currencies=["EURO"])

    def test_exchange_rate_filters_empty_target_currencies(self):
        """Test exchange rate config filters out empty target currencies."""
        config = ExchangeRateWidgetConfig(
            base_currency="USD",
            target_currencies=["EUR", "", "  ", "GBP"]
        )
        assert len(config.target_currencies) == 2
        assert config.target_currencies == ["EUR", "GBP"]

    def test_exchange_rate_too_many_target_currencies(self):
        """Test exchange rate config limits number of target currencies."""
        with pytest.raises(ValidationError):
            ExchangeRateWidgetConfig(
                base_currency="USD",
                target_currencies=[f"C{i:02d}" for i in range(21)]
            )


class TestMarketWidgetConfig:
    """Tests for MarketWidgetConfig validation."""

    def test_valid_market_config_with_stocks(self):
        """Test valid market widget config with stocks."""
        config = MarketWidgetConfig(
            stocks=["AAPL", "GOOGL", "MSFT"],
            crypto=[]
        )
        assert len(config.stocks) == 3
        assert config.crypto == []

    def test_valid_market_config_with_crypto(self):
        """Test valid market widget config with crypto."""
        config = MarketWidgetConfig(
            stocks=[],
            crypto=["BTC", "ETH", "SOL"]
        )
        assert config.stocks == []
        assert len(config.crypto) == 3

    def test_valid_market_config_with_both(self):
        """Test valid market widget config with both stocks and crypto."""
        config = MarketWidgetConfig(
            stocks=["AAPL", "^GSPC"],
            crypto=["BTC", "ETH"]
        )
        assert len(config.stocks) == 2
        assert len(config.crypto) == 2

    def test_market_config_no_sources(self):
        """Test market config requires at least one source."""
        with pytest.raises(ValueError) as exc_info:
            MarketWidgetConfig(stocks=[], crypto=[])
        assert "at least one" in str(exc_info.value).lower()

    def test_market_config_normalizes_symbols(self):
        """Test market config normalizes symbols to uppercase."""
        config = MarketWidgetConfig(stocks=["aapl"], crypto=["btc"])
        assert config.stocks == ["AAPL"]
        assert config.crypto == ["BTC"]

    def test_market_config_filters_empty_symbols(self):
        """Test market config filters out empty symbols."""
        config = MarketWidgetConfig(
            stocks=["AAPL", "", "  ", "GOOGL"],
            crypto=["BTC", "", "ETH"]
        )
        assert len(config.stocks) == 2
        assert config.stocks == ["AAPL", "GOOGL"]
        assert len(config.crypto) == 2
        assert config.crypto == ["BTC", "ETH"]

    def test_market_config_stock_symbol_too_long(self):
        """Test market config rejects stock symbols that are too long."""
        with pytest.raises(ValidationError):
            MarketWidgetConfig(stocks=["A" * 11])

    def test_market_config_crypto_symbol_too_long(self):
        """Test market config rejects crypto symbols that are too long."""
        with pytest.raises(ValidationError):
            MarketWidgetConfig(crypto=["B" * 11])

    def test_market_config_allows_special_stock_symbols(self):
        """Test market config allows special characters in stock symbols."""
        config = MarketWidgetConfig(stocks=["^GSPC", "BRK.B"])
        assert config.stocks == ["^GSPC", "BRK.B"]

    def test_market_config_too_many_stocks(self):
        """Test market config limits number of stocks."""
        with pytest.raises(ValidationError):
            MarketWidgetConfig(stocks=[f"STOCK{i}" for i in range(21)])

    def test_market_config_too_many_crypto(self):
        """Test market config limits number of crypto."""
        with pytest.raises(ValidationError):
            MarketWidgetConfig(crypto=[f"CRYPTO{i}" for i in range(21)])


class TestValidateWidgetConfig:
    """Tests for validate_widget_config function."""

    def test_validate_weather_config(self):
        """Test validating weather widget config."""
        config_dict = {"location": "Prague", "units": "metric"}
        validated = validate_widget_config("weather", config_dict)
        assert validated["location"] == "Prague"
        assert validated["units"] == "metric"
        assert validated["show_forecast"] is True  # default value

    def test_validate_news_config(self):
        """Test validating news widget config."""
        config_dict = {
            "rss_feeds": ["https://example.com/feed.xml"],
            "max_articles": 15
        }
        validated = validate_widget_config("news", config_dict)
        assert len(validated["rss_feeds"]) == 1
        assert validated["max_articles"] == 15

    def test_validate_exchange_rate_config(self):
        """Test validating exchange rate widget config."""
        config_dict = {
            "base_currency": "usd",
            "target_currencies": ["eur", "gbp"]
        }
        validated = validate_widget_config("exchange_rate", config_dict)
        assert validated["base_currency"] == "USD"
        assert validated["target_currencies"] == ["EUR", "GBP"]

    def test_validate_market_config(self):
        """Test validating market widget config."""
        config_dict = {
            "stocks": ["aapl", "googl"],
            "crypto": ["btc"]
        }
        validated = validate_widget_config("market", config_dict)
        assert validated["stocks"] == ["AAPL", "GOOGL"]
        assert validated["crypto"] == ["BTC"]

    def test_validate_unknown_widget_type(self):
        """Test validating unknown widget type raises error."""
        with pytest.raises(ValueError) as exc_info:
            validate_widget_config("unknown", {})
        assert "unknown widget type" in str(exc_info.value).lower()

    def test_validate_invalid_config_raises_validation_error(self):
        """Test validating invalid config raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_widget_config("weather", {"units": "invalid"})
