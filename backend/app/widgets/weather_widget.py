"""Weather widget implementation."""

from typing import Any, Dict, Optional

import aiohttp

from app.config import settings
from app.logging_config import get_logger
from app.widgets.base_widget import BaseWidget

logger = get_logger(__name__)


class WeatherWidget(BaseWidget):
    """Widget for displaying weather information."""

    widget_type = "weather"

    def validate_config(self) -> bool:
        """Validate weather widget configuration."""
        required_fields = ["location"]

        # Check if API key is available (from config or settings)
        api_key = self.config.get("api_key") or settings.WEATHER_API_KEY
        if not api_key:
            logger.warning(
                "Weather API key not configured",
                extra={"widget_type": self.widget_type, "widget_id": self.widget_id},
            )
            return False

        # Check required fields
        for field in required_fields:
            if field not in self.config:
                logger.warning(
                    f"Missing required field: {field}",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "missing_field": field,
                    },
                )
                return False

        logger.debug(
            "Weather widget configuration validated",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "location": self.config.get("location"),
            },
        )
        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch weather data from OpenWeatherMap API.

        Returns:
            Dictionary containing weather data
        """
        api_key = self.config.get("api_key") or settings.WEATHER_API_KEY
        location = self.config.get("location")
        units = self.config.get("units", "metric")  # metric, imperial, or standard
        show_forecast = self.config.get("show_forecast", True)

        # Build API URL for current weather
        current_url = "https://api.openweathermap.org/data/2.5/weather"
        current_params = {"q": location, "units": units, "appid": api_key}

        logger.info(
            "Fetching weather data from OpenWeatherMap",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "location": location,
                "units": units,
                "api_url": current_url,
            },
        )

        async with aiohttp.ClientSession() as session:
            # Fetch current weather
            async with session.get(current_url, params=current_params) as response:
                logger.debug(
                    "Weather API response received",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "response_status": response.status,
                        "api_url": current_url,
                    },
                )

                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(
                        f"Weather API returned error: {response.status}",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "response_status": response.status,
                            "error_text": error_text,
                            "api_url": current_url,
                        },
                    )
                    raise Exception(f"Weather API error: {response.status} - {error_text}")

                current_data = await response.json()

            # Fetch forecast if enabled
            forecast_data = None
            if show_forecast:
                # Get coordinates from current weather response
                lat = current_data["coord"]["lat"]
                lon = current_data["coord"]["lon"]

                forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
                forecast_params = {"lat": lat, "lon": lon, "units": units, "appid": api_key}

                logger.debug(
                    "Fetching weather forecast data",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "coordinates": {"lat": lat, "lon": lon},
                        "api_url": forecast_url,
                    },
                )

                async with session.get(forecast_url, params=forecast_params) as response:
                    if response.status == 200:
                        forecast_data = await response.json()
                        logger.debug(
                            "Weather forecast data retrieved successfully",
                            extra={
                                "widget_type": self.widget_type,
                                "widget_id": self.widget_id,
                                "response_status": response.status,
                            },
                        )
                    else:
                        logger.warning(
                            f"Failed to fetch weather forecast: {response.status}",
                            extra={
                                "widget_type": self.widget_type,
                                "widget_id": self.widget_id,
                                "response_status": response.status,
                                "api_url": forecast_url,
                            },
                        )

        # Transform data to widget format
        return self.transform_data(current_data, forecast_data)

    def transform_data(
        self, current: Dict[str, Any], forecast: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform OpenWeatherMap data to widget format.

        Args:
            current: Current weather data
            forecast: Forecast data (optional)

        Returns:
            Transformed weather data
        """
        units = self.config.get("units", "metric")
        temp_unit = "°C" if units == "metric" else "°F" if units == "imperial" else "K"

        result = {
            "location": {
                "name": current["name"],
                "country": current["sys"]["country"],
                "coordinates": {"lat": current["coord"]["lat"], "lon": current["coord"]["lon"]},
                "timezone": current.get("timezone", 0),  # Timezone offset in seconds from UTC
            },
            "current": {
                "temperature": round(current["main"]["temp"], 1),
                "feels_like": round(current["main"]["feels_like"], 1),
                "temp_min": round(current["main"]["temp_min"], 1),
                "temp_max": round(current["main"]["temp_max"], 1),
                "temp_unit": temp_unit,
                "pressure": current["main"]["pressure"],
                "humidity": current["main"]["humidity"],
                "description": current["weather"][0]["description"],
                "icon": current["weather"][0]["icon"],
                "wind_speed": current["wind"]["speed"],
                "clouds": current["clouds"]["all"],
            },
        }

        # Add forecast if available
        if forecast and "list" in forecast:
            # Group forecast by day (take one reading per day, around noon)
            daily_forecast = []
            processed_dates = set()

            for item in forecast["list"]:
                # Extract date (YYYY-MM-DD)
                date = item["dt_txt"].split(" ")[0]
                time = item["dt_txt"].split(" ")[1]

                # Take the forecast around 12:00 for each day
                if date not in processed_dates and "12:00" in time:
                    daily_forecast.append(
                        {
                            "date": date,
                            "temperature": round(item["main"]["temp"], 1),
                            "temp_min": round(item["main"]["temp_min"], 1),
                            "temp_max": round(item["main"]["temp_max"], 1),
                            "temp_unit": temp_unit,
                            "description": item["weather"][0]["description"],
                            "icon": item["weather"][0]["icon"],
                            "humidity": item["main"]["humidity"],
                        }
                    )
                    processed_dates.add(date)

                # Limit to 5 days
                if len(daily_forecast) >= 5:
                    break

            result["forecast"] = daily_forecast

        return result
