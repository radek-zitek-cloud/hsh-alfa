"""Widget implementations."""

from app.widgets.base_widget import BaseWidget
from app.widgets.exchange_rate_widget import ExchangeRateWidget
from app.widgets.habit_tracking_widget import HabitTrackingWidget
from app.widgets.market_widget import MarketWidget
from app.widgets.news_widget import NewsWidget
from app.widgets.weather_widget import WeatherWidget


def register_all_widgets():
    """Register all available widget types."""
    from app.services.widget_registry import widget_registry

    widget_registry.register(WeatherWidget)
    widget_registry.register(ExchangeRateWidget)
    widget_registry.register(NewsWidget)
    widget_registry.register(MarketWidget)
    widget_registry.register(HabitTrackingWidget)


__all__ = [
    "BaseWidget",
    "WeatherWidget",
    "ExchangeRateWidget",
    "NewsWidget",
    "MarketWidget",
    "HabitTrackingWidget",
    "register_all_widgets",
]
