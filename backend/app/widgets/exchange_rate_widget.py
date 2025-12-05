"""Exchange rate widget implementation."""

from typing import Any, Dict, List

import aiohttp

from app.logging_config import get_logger
from app.widgets.base_widget import BaseWidget

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
                        "missing_field": field,
                    },
                )
                return False

        # Validate target_currencies is a list
        if not isinstance(self.config.get("target_currencies"), list):
            logger.warning(
                "target_currencies must be a list",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "field_type": type(self.config.get("target_currencies")).__name__,
                },
            )
            return False

        logger.debug(
            "Exchange rate widget configuration validated",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "base_currency": self.config.get("base_currency"),
                "target_currencies": len(self.config.get("target_currencies", [])),
            },
        )
        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch exchange rate data from Yahoo Finance.

        Returns:
            Dictionary containing exchange rate data
        """
        base_currency = self.config.get("base_currency", "USD")
        target_currencies = self.config.get("target_currencies", [])

        logger.info(
            "Fetching exchange rates from Yahoo Finance",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "base_currency": base_currency,
                "num_targets": len(target_currencies),
            },
        )

        data = await self._fetch_from_yahoo_finance(base_currency, target_currencies)
        return self.transform_data(data, target_currencies)

    async def _fetch_from_yahoo_finance(
        self, base_currency: str, target_currencies: List[str]
    ) -> Dict[str, Any]:
        """
        Fetch exchange rates from Yahoo Finance (free, no API key required).

        Args:
            base_currency: Base currency code
            target_currencies: List of target currency codes

        Returns:
            Exchange rate data
        """
        rates = {}
        base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

        # Add headers to avoid being blocked by Yahoo Finance
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for target_currency in target_currencies:
                try:
                    # Yahoo Finance format for currency pairs: EURUSD=X
                    symbol = f"{base_currency}{target_currency}=X"
                    url = f"{base_url}/{symbol}"
                    params = {
                        "interval": "1d",
                        "range": "1d",
                    }

                    logger.debug(
                        "Fetching exchange rate from Yahoo Finance",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "symbol": symbol,
                            "api_url": url,
                        },
                    )

                    async with session.get(url, params=params) as response:
                        logger.debug(
                            "Yahoo Finance response received",
                            extra={
                                "widget_type": self.widget_type,
                                "widget_id": self.widget_id,
                                "symbol": symbol,
                                "response_status": response.status,
                                "api_url": url,
                            },
                        )

                        if response.status != 200:
                            logger.warning(
                                f"Failed to fetch {symbol}: {response.status}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "symbol": symbol,
                                    "response_status": response.status,
                                    "api_url": url,
                                },
                            )
                            continue

                        data = await response.json()

                        # Extract rate from Yahoo Finance response
                        chart = data.get("chart", {})
                        result = chart.get("result", [])

                        if not result:
                            logger.warning(
                                f"No data for currency pair {symbol}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "symbol": symbol,
                                },
                            )
                            continue

                        quote_data = result[0]
                        meta = quote_data.get("meta", {})

                        # Get current exchange rate
                        current_rate = meta.get("regularMarketPrice")

                        if current_rate is None:
                            logger.warning(
                                f"No rate data for {symbol}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "symbol": symbol,
                                },
                            )
                            continue

                        rates[target_currency] = current_rate

                        logger.debug(
                            "Exchange rate retrieved",
                            extra={
                                "widget_type": self.widget_type,
                                "widget_id": self.widget_id,
                                "symbol": symbol,
                                "rate": current_rate,
                            },
                        )

                except Exception as e:
                    logger.error(
                        f"Error fetching {target_currency}: {str(e)}",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "target_currency": target_currency,
                            "error_type": type(e).__name__,
                        },
                        exc_info=True,
                    )
                    continue

        logger.info(
            "Yahoo Finance data fetch completed",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "currencies_requested": len(target_currencies),
                "currencies_retrieved": len(rates),
            },
        )

        # Build response in similar format to exchangerate-api
        return {
            "result": "success",
            "base_code": base_currency,
            "conversion_rates": rates,
            "time_last_update_utc": self.get_timestamp(),
        }

    def transform_data(
        self, raw_data: Dict[str, Any], target_currencies: List[str]
    ) -> Dict[str, Any]:
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
                rates.append(
                    {
                        "currency": currency,
                        "rate": round(rate_value, 4),
                        "reverse_rate": round(reverse_rate, 4),
                        "formatted": f"1 {base_currency} = {rate_value:.4f} {currency}",
                    }
                )
            else:
                logger.warning(
                    f"Currency {currency} not found in exchange rate data",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "missing_currency": currency,
                        "base_currency": base_currency,
                    },
                )

        result = {
            "base_currency": base_currency,
            "rates": rates,
            "last_update": raw_data.get("time_last_update_utc", self.get_timestamp()),
        }

        return result
