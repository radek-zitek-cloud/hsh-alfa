"""Unit tests for widget functionality."""

import pytest

from app.widgets.exchange_rate_widget import ExchangeRateWidget
from app.widgets.weather_widget import WeatherWidget


def test_weather_widget_validation_without_api_key():
    """Test weather widget fails validation without API key."""
    widget = WeatherWidget(widget_id="test-weather", config={"location": "Prague"})
    assert not widget.validate_config()


def test_weather_widget_validation_with_api_key():
    """Test weather widget passes validation with API key."""
    widget = WeatherWidget(
        widget_id="test-weather", config={"location": "Prague", "api_key": "test-api-key-12345"}
    )
    assert widget.validate_config()


def test_weather_widget_validation_without_location():
    """Test weather widget fails validation without location."""
    widget = WeatherWidget(widget_id="test-weather", config={"api_key": "test-key"})
    assert not widget.validate_config()


def test_exchange_widget_with_default_config():
    """Test exchange rate widget with default configuration."""
    widget = ExchangeRateWidget(widget_id="test-exchange", config={})
    # Should pass validation with defaults
    assert widget.validate_config()


def test_exchange_widget_with_custom_currencies():
    """Test exchange rate widget with custom currencies."""
    widget = ExchangeRateWidget(
        widget_id="test-exchange",
        config={"base_currency": "USD", "target_currencies": ["EUR", "GBP", "JPY"]},
    )
    assert widget.validate_config()
    assert widget.config["base_currency"] == "USD"
    assert len(widget.config["target_currencies"]) == 3


def test_widget_cache_key_generation():
    """Test that widgets generate unique cache keys."""
    widget1 = WeatherWidget(widget_id="weather-1", config={"location": "Prague", "api_key": "key1"})
    widget2 = WeatherWidget(widget_id="weather-2", config={"location": "London", "api_key": "key2"})

    # Different widgets should have different cache keys
    assert widget1.get_cache_key() != widget2.get_cache_key()


def test_widget_cache_key_consistency():
    """Test that same widget config generates same cache key."""
    config = {"location": "Prague", "api_key": "key"}

    widget1 = WeatherWidget(widget_id="test", config=config)
    widget2 = WeatherWidget(widget_id="test", config=config)

    # Same config should produce same cache key
    assert widget1.get_cache_key() == widget2.get_cache_key()


def test_widget_enabled_flag():
    """Test widget enabled/disabled flag."""
    widget = WeatherWidget(
        widget_id="test-weather", config={"location": "Prague", "api_key": "key"}, enabled=False
    )
    assert not widget.enabled

    widget.enabled = True
    assert widget.enabled
