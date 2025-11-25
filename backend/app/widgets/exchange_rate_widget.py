"""Exchange rate widget implementation."""
import aiohttp
from typing import Dict, Any, List
from app.widgets.base_widget import BaseWidget
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class ExchangeRateWidget(BaseWidget):
    """Widget for displaying exchange rates."""

    widget_type = "exchange_rate"

    def validate_config(self) -> bool:
        """Validate exchange rate widget configuration."""
        required_fields = ["base_currency", "target_currencies"]

        # Check required fields
        for field in required_fields:
            if field not in self.config:
                logger.warning(
                    f"Missing required field: {field}",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "missing_field": field
                    }
                )
                return False

        # Validate target_currencies is a list
        if not isinstance(self.config.get("target_currencies"), list):
            logger.warning(
                "target_currencies must be a list",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "field_type": type(self.config.get("target_currencies")).__name__
                }
            )
            return False

        logger.debug(
            "Exchange rate widget configuration validated",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "base_currency": self.config.get("base_currency"),
                "target_currencies": len(self.config.get("target_currencies", []))
            }
        )
        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch exchange rate data from exchangerate-api.com.

        Returns:
            Dictionary containing exchange rate data
        """
        base_currency = self.config.get("base_currency", "USD")
        target_currencies = self.config.get("target_currencies", [])
        show_trend = self.config.get("show_trend", False)
        api_key = self.config.get("api_key") or settings.EXCHANGE_RATE_API_KEY

        # Use free API if no key provided (European Central Bank)
        if not api_key:
            logger.info(
                "No API key provided, using ECB free API",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "base_currency": base_currency
                }
            )
            return await self._fetch_from_ecb(base_currency, target_currencies)

        # Use exchangerate-api.com with API key
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

        logger.info(
            "Fetching exchange rates from exchangerate-api.com",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "base_currency": base_currency,
                "api_url": url
            }
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.debug(
                    "Exchange rate API response received",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "response_status": response.status,
                        "api_url": url
                    }
                )

                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(
                        f"Exchange rate API returned error: {response.status}",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "response_status": response.status,
                            "error_text": error_text,
                            "api_url": url
                        }
                    )
                    raise Exception(f"Exchange rate API error: {response.status} - {error_text}")

                data = await response.json()

        # Transform data to widget format
        return self.transform_data(data, target_currencies)

    async def _fetch_from_ecb(self, base_currency: str, target_currencies: List[str]) -> Dict[str, Any]:
        """
        Fetch exchange rates from European Central Bank (free, no API key).

        Args:
            base_currency: Base currency code
            target_currencies: List of target currency codes

        Returns:
            Exchange rate data
        """
        # ECB provides rates with EUR as base
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

        logger.info(
            "Fetching exchange rates from European Central Bank (free API)",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "base_currency": base_currency,
                "api_url": url
            }
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.debug(
                    "ECB API response received",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "response_status": response.status,
                        "api_url": url
                    }
                )

                if response.status != 200:
                    logger.warning(
                        f"ECB API returned error: {response.status}",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "response_status": response.status,
                            "api_url": url
                        }
                    )
                    raise Exception(f"ECB API error: {response.status}")

                xml_data = await response.text()

        # Parse XML (simple parsing for the ECB format)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)

        # Extract rates from XML
        rates = {"EUR": 1.0}
        for cube in root.findall(".//{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube[@currency]"):
            currency = cube.get("currency")
            rate = float(cube.get("rate"))
            rates[currency] = rate

        logger.debug(
            "ECB exchange rates parsed",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "num_rates": len(rates)
            }
        )

        # Convert to requested base currency
        if base_currency != "EUR":
            if base_currency not in rates:
                logger.warning(
                    f"Base currency {base_currency} not available in ECB data",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "base_currency": base_currency,
                        "available_currencies": list(rates.keys())
                    }
                )
                raise Exception(f"Base currency {base_currency} not available in ECB data")

            base_rate = rates[base_currency]
            # Convert all rates to the new base
            converted_rates = {}
            for currency, rate in rates.items():
                converted_rates[currency] = rate / base_rate
            rates = converted_rates

            logger.debug(
                "Exchange rates converted to requested base currency",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "base_currency": base_currency
                }
            )

        # Build response in similar format to exchangerate-api
        return {
            "result": "success",
            "base_code": base_currency,
            "conversion_rates": rates,
            "time_last_update_utc": self.get_timestamp()
        }

    def transform_data(self, raw_data: Dict[str, Any], target_currencies: List[str]) -> Dict[str, Any]:
        """
        Transform exchange rate data to widget format.

        Args:
            raw_data: Raw API response
            target_currencies: List of currencies to display

        Returns:
            Transformed exchange rate data
        """
        base_currency = raw_data.get("base_code", self.config.get("base_currency"))
        all_rates = raw_data.get("conversion_rates", {})

        # Filter to only target currencies
        rates = []
        for currency in target_currencies:
            if currency in all_rates:
                rate_value = all_rates[currency]
                reverse_rate = 1 / rate_value if rate_value != 0 else 0
                rates.append({
                    "currency": currency,
                    "rate": round(rate_value, 4),
                    "reverse_rate": round(reverse_rate, 4),
                    "formatted": f"1 {base_currency} = {rate_value:.4f} {currency}"
                })
            else:
                logger.warning(
                    f"Currency {currency} not found in exchange rate data",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "missing_currency": currency,
                        "base_currency": base_currency
                    }
                )

        result = {
            "base_currency": base_currency,
            "rates": rates,
            "last_update": raw_data.get("time_last_update_utc", self.get_timestamp())
        }

        return result
