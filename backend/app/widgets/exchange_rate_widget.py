"""Exchange rate widget implementation."""
import aiohttp
import logging
from typing import Dict, Any, List
from app.widgets.base_widget import BaseWidget
from app.config import settings

logger = logging.getLogger(__name__)


class ExchangeRateWidget(BaseWidget):
    """Widget for displaying exchange rates."""

    widget_type = "exchange_rate"

    def validate_config(self) -> bool:
        """Validate exchange rate widget configuration."""
        required_fields = ["base_currency", "target_currencies"]

        # Check required fields
        for field in required_fields:
            if field not in self.config:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate target_currencies is a list
        if not isinstance(self.config.get("target_currencies"), list):
            logger.error("target_currencies must be a list")
            return False

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
            return await self._fetch_from_ecb(base_currency, target_currencies)

        # Use exchangerate-api.com with API key
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
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

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
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

        # Convert to requested base currency
        if base_currency != "EUR":
            if base_currency not in rates:
                raise Exception(f"Base currency {base_currency} not available in ECB data")

            base_rate = rates[base_currency]
            # Convert all rates to the new base
            converted_rates = {}
            for currency, rate in rates.items():
                converted_rates[currency] = rate / base_rate
            rates = converted_rates

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
                rates.append({
                    "currency": currency,
                    "rate": round(rate_value, 4),
                    "formatted": f"1 {base_currency} = {rate_value:.4f} {currency}"
                })
            else:
                logger.warning(f"Currency {currency} not found in exchange rate data")

        result = {
            "base_currency": base_currency,
            "rates": rates,
            "last_update": raw_data.get("time_last_update_utc", self.get_timestamp())
        }

        return result
