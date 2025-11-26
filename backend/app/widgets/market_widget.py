"""Market information widget implementation."""

from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from app.logging_config import get_logger
from app.widgets.base_widget import BaseWidget

logger = get_logger(__name__)


class MarketWidget(BaseWidget):
    """Widget for displaying market information (stocks, indices, crypto)."""

    widget_type = "market"

    def validate_config(self) -> bool:
        """Validate market widget configuration."""
        # At least one of stocks or crypto must be configured
        has_stocks = "stocks" in self.config and isinstance(self.config["stocks"], list)
        has_crypto = "crypto" in self.config and isinstance(self.config["crypto"], list)

        if not has_stocks and not has_crypto:
            logger.warning(
                "Market widget must have either 'stocks' or 'crypto' configured",
                extra={"widget_type": self.widget_type, "widget_id": self.widget_id},
            )
            return False

        # Filter out empty symbols from stocks and crypto lists
        if has_stocks:
            self.config["stocks"] = [s for s in self.config["stocks"] if s and s.strip()]
        if has_crypto:
            self.config["crypto"] = [c for c in self.config["crypto"] if c and c.strip()]

        # Re-check if we still have valid data after filtering
        has_valid_stocks = has_stocks and len(self.config["stocks"]) > 0
        has_valid_crypto = has_crypto and len(self.config["crypto"]) > 0

        if not has_valid_stocks and not has_valid_crypto:
            logger.warning(
                "Market widget must have at least one valid stock or crypto symbol",
                extra={"widget_type": self.widget_type, "widget_id": self.widget_id},
            )
            return False

        logger.debug(
            "Market widget configuration validated",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "has_stocks": has_valid_stocks,
                "num_stocks": len(self.config.get("stocks", [])),
                "has_crypto": has_valid_crypto,
                "num_crypto": len(self.config.get("crypto", [])),
            },
        )
        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch market data from Yahoo Finance API (free, no key required).

        Returns:
            Dictionary containing market data
        """
        stocks = self.config.get("stocks", [])
        crypto = self.config.get("crypto", [])

        logger.info(
            "Fetching market data",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "num_stocks": len(stocks),
                "num_crypto": len(crypto),
            },
        )

        result = {"stocks": [], "crypto": []}

        # Fetch stock data
        if stocks:
            logger.debug(
                "Fetching stock data from Yahoo Finance",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "num_stocks": len(stocks),
                },
            )
            stock_data = await self._fetch_yahoo_finance(stocks)
            result["stocks"] = stock_data
            logger.debug(
                "Stock data retrieved",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "stocks_retrieved": len(stock_data),
                },
            )

        # Fetch crypto data (using Coinbase API - free, no key)
        if crypto:
            logger.debug(
                "Fetching crypto data from CoinGecko",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "num_crypto": len(crypto),
                },
            )
            crypto_data = await self._fetch_crypto_data(crypto)
            result["crypto"] = crypto_data
            logger.debug(
                "Crypto data retrieved",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "crypto_retrieved": len(crypto_data),
                },
            )

        return result

    async def _fetch_yahoo_finance(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch stock data from Yahoo Finance API.

        Args:
            symbols: List of stock symbols (e.g., ["^GSPC", "AAPL", "GOOGL"])

        Returns:
            List of stock data dictionaries
        """
        results = []

        # Yahoo Finance query API
        base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

        # Add headers to avoid being blocked by Yahoo Finance
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for symbol in symbols:
                try:
                    # Fetch YTD data to get all historical data we need
                    url = f"{base_url}/{symbol}"
                    params = {
                        "interval": "1d",
                        "range": "1y",  # Get 1 year for YTD, 30d, and 5d calculations
                    }

                    logger.debug(
                        "Fetching stock data from Yahoo Finance",
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

                        # Extract relevant data
                        chart = data.get("chart", {})
                        result = chart.get("result", [])

                        if not result:
                            logger.warning(
                                f"No data for symbol {symbol}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "symbol": symbol,
                                },
                            )
                            continue

                        quote_data = result[0]
                        meta = quote_data.get("meta", {})
                        indicators = quote_data.get("indicators", {})
                        quote = indicators.get("quote", [{}])[0]
                        timestamps = quote_data.get("timestamp", [])

                        # Get current price
                        current_price = meta.get("regularMarketPrice")
                        previous_close = meta.get("previousClose")

                        if current_price is None:
                            logger.warning(
                                f"No price data for {symbol}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "symbol": symbol,
                                },
                            )
                            continue

                        # Calculate 1-day change
                        change = None
                        change_percent = None
                        if previous_close:
                            change = current_price - previous_close
                            change_percent = (change / previous_close) * 100

                        # Get historical prices for period calculations
                        close_prices = quote.get("close", [])

                        # Calculate period changes
                        change_5d_percent = self._calculate_period_change(
                            current_price, close_prices, timestamps, days=5
                        )
                        change_30d_percent = self._calculate_period_change(
                            current_price, close_prices, timestamps, days=30
                        )
                        change_ytd_percent = self._calculate_ytd_change(
                            current_price, close_prices, timestamps
                        )

                        results.append(
                            {
                                "symbol": symbol,
                                "name": meta.get("longName") or meta.get("shortName") or symbol,
                                "price": round(current_price, 2),
                                "change": round(change, 2) if change else None,
                                "change_percent": (
                                    round(change_percent, 2) if change_percent else None
                                ),
                                "change_5d_percent": (
                                    round(change_5d_percent, 2)
                                    if change_5d_percent is not None
                                    else None
                                ),
                                "change_30d_percent": (
                                    round(change_30d_percent, 2)
                                    if change_30d_percent is not None
                                    else None
                                ),
                                "change_ytd_percent": (
                                    round(change_ytd_percent, 2)
                                    if change_ytd_percent is not None
                                    else None
                                ),
                                "currency": meta.get("currency", "USD"),
                                "market_state": meta.get("marketState", "REGULAR"),
                            }
                        )

                except Exception as e:
                    logger.error(
                        f"Error fetching {symbol}: {str(e)}",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "symbol": symbol,
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
                "symbols_requested": len(symbols),
                "symbols_retrieved": len(results),
            },
        )

        return results

    def _calculate_period_change(
        self, current_price: float, close_prices: List[float], timestamps: List[int], days: int
    ) -> float:
        """
        Calculate percentage change for a given period.

        Args:
            current_price: Current price
            close_prices: List of historical close prices
            timestamps: List of timestamps corresponding to prices
            days: Number of days to look back

        Returns:
            Percentage change, or None if data is insufficient
        """
        if not close_prices or not timestamps:
            return None

        # Convert timestamps to datetime and find the target date
        current_time = datetime.now()
        target_time = current_time.timestamp() - (days * 24 * 60 * 60)

        # Find the closest price to the target time
        closest_idx = None
        closest_diff = float("inf")

        for idx, ts in enumerate(timestamps):
            if close_prices[idx] is None:  # Skip None values
                continue

            diff = abs(ts - target_time)
            if diff < closest_diff:
                closest_diff = diff
                closest_idx = idx

        if closest_idx is None:
            return None

        historical_price = close_prices[closest_idx]
        if historical_price and historical_price > 0:
            return ((current_price - historical_price) / historical_price) * 100

        return None

    def _calculate_ytd_change(
        self, current_price: float, close_prices: List[float], timestamps: List[int]
    ) -> float:
        """
        Calculate year-to-date percentage change.

        Args:
            current_price: Current price
            close_prices: List of historical close prices
            timestamps: List of timestamps corresponding to prices

        Returns:
            YTD percentage change, or None if data is insufficient
        """
        if not close_prices or not timestamps:
            return None

        # Find the first trading day of the current year
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1).timestamp()

        # Find the first price after year start
        year_start_idx = None
        for idx, ts in enumerate(timestamps):
            if close_prices[idx] is None:  # Skip None values
                continue

            if ts >= year_start:
                year_start_idx = idx
                break

        if year_start_idx is None:
            return None

        year_start_price = close_prices[year_start_idx]
        if year_start_price and year_start_price > 0:
            return ((current_price - year_start_price) / year_start_price) * 100

        return None

    async def _fetch_crypto_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch cryptocurrency data from CoinGecko API (free, no key required).

        Args:
            symbols: List of crypto symbols (e.g., ["BTC", "ETH", "SOL"])

        Returns:
            List of crypto data dictionaries
        """
        results = []

        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "ADA": "cardano",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "AVAX": "avalanche-2",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "XRP": "ripple",
        }

        # Convert symbols to IDs
        id_to_symbol = {}
        crypto_ids = []
        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper in symbol_map:
                crypto_id = symbol_map[symbol_upper]
                crypto_ids.append(crypto_id)
                id_to_symbol[crypto_id] = symbol_upper
            else:
                # Try to use as lowercase ID directly
                crypto_id = symbol.lower()
                crypto_ids.append(crypto_id)
                id_to_symbol[crypto_id] = symbol.upper()

        if not crypto_ids:
            logger.warning(
                "No valid crypto IDs after mapping",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "requested_symbols": len(symbols),
                },
            )
            return results

        async with aiohttp.ClientSession() as session:
            # Fetch current prices and 24h change
            price_url = "https://api.coingecko.com/api/v3/simple/price"
            price_params = {
                "ids": ",".join(crypto_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }

            logger.info(
                "Fetching crypto data from CoinGecko API",
                extra={
                    "widget_type": self.widget_type,
                    "widget_id": self.widget_id,
                    "num_crypto": len(crypto_ids),
                    "api_url": price_url,
                },
            )

            try:
                async with session.get(price_url, params=price_params) as response:
                    logger.debug(
                        "CoinGecko API response received",
                        extra={
                            "widget_type": self.widget_type,
                            "widget_id": self.widget_id,
                            "response_status": response.status,
                            "api_url": price_url,
                        },
                    )

                    if response.status != 200:
                        logger.warning(
                            f"CoinGecko API error: {response.status}",
                            extra={
                                "widget_type": self.widget_type,
                                "widget_id": self.widget_id,
                                "response_status": response.status,
                                "api_url": price_url,
                            },
                        )
                        return results

                    price_data = await response.json()

                    # For each crypto, fetch historical data for period calculations
                    for crypto_id in crypto_ids:
                        if crypto_id not in price_data:
                            logger.warning(
                                f"No data for crypto {id_to_symbol[crypto_id]}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "crypto_id": crypto_id,
                                    "symbol": id_to_symbol[crypto_id],
                                },
                            )
                            continue

                        current_data = price_data[crypto_id]
                        price = current_data.get("usd")
                        change_24h = current_data.get("usd_24h_change")

                        if price is None:
                            continue

                        # Fetch historical data for period calculations
                        market_chart_url = (
                            f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
                        )
                        market_params = {
                            "vs_currency": "usd",
                            "days": "365",  # Get 1 year for YTD calculation
                            "interval": "daily",
                        }

                        change_5d = None
                        change_30d = None
                        change_ytd = None

                        try:
                            logger.debug(
                                "Fetching historical crypto data from CoinGecko",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "crypto_id": crypto_id,
                                    "symbol": id_to_symbol[crypto_id],
                                    "api_url": market_chart_url,
                                },
                            )

                            async with session.get(
                                market_chart_url, params=market_params
                            ) as hist_response:
                                if hist_response.status == 200:
                                    hist_data = await hist_response.json()
                                    prices = hist_data.get("prices", [])

                                    if prices:
                                        # Calculate period changes
                                        change_5d = self._calculate_crypto_period_change(
                                            price, prices, days=5
                                        )
                                        change_30d = self._calculate_crypto_period_change(
                                            price, prices, days=30
                                        )
                                        change_ytd = self._calculate_crypto_ytd_change(
                                            price, prices
                                        )

                                        logger.debug(
                                            "Historical crypto data retrieved and calculated",
                                            extra={
                                                "widget_type": self.widget_type,
                                                "widget_id": self.widget_id,
                                                "crypto_id": crypto_id,
                                                "symbol": id_to_symbol[crypto_id],
                                                "num_data_points": len(prices),
                                            },
                                        )
                                else:
                                    logger.warning(
                                        f"Failed to fetch historical data for {crypto_id}: {hist_response.status}",
                                        extra={
                                            "widget_type": self.widget_type,
                                            "widget_id": self.widget_id,
                                            "crypto_id": crypto_id,
                                            "symbol": id_to_symbol[crypto_id],
                                            "response_status": hist_response.status,
                                            "api_url": market_chart_url,
                                        },
                                    )
                        except Exception as e:
                            logger.error(
                                f"Error fetching historical data for {crypto_id}: {str(e)}",
                                extra={
                                    "widget_type": self.widget_type,
                                    "widget_id": self.widget_id,
                                    "crypto_id": crypto_id,
                                    "symbol": id_to_symbol[crypto_id],
                                    "error_type": type(e).__name__,
                                    "api_url": market_chart_url,
                                },
                                exc_info=True,
                            )

                        results.append(
                            {
                                "symbol": id_to_symbol[crypto_id],
                                "name": id_to_symbol[crypto_id],
                                "price": round(price, 2) if price >= 1 else round(price, 6),
                                "change": None,  # Not directly available
                                "change_percent": round(change_24h, 2) if change_24h else None,
                                "change_5d_percent": (
                                    round(change_5d, 2) if change_5d is not None else None
                                ),
                                "change_30d_percent": (
                                    round(change_30d, 2) if change_30d is not None else None
                                ),
                                "change_ytd_percent": (
                                    round(change_ytd, 2) if change_ytd is not None else None
                                ),
                                "currency": "USD",
                                "market_state": "24/7",
                            }
                        )

            except Exception as e:
                logger.error(
                    f"Error fetching crypto data: {str(e)}",
                    extra={
                        "widget_type": self.widget_type,
                        "widget_id": self.widget_id,
                        "error_type": type(e).__name__,
                        "api_url": price_url,
                    },
                    exc_info=True,
                )

        logger.info(
            "CoinGecko data fetch completed",
            extra={
                "widget_type": self.widget_type,
                "widget_id": self.widget_id,
                "crypto_requested": len(symbols),
                "crypto_retrieved": len(results),
            },
        )

        return results

    def _calculate_crypto_period_change(
        self, current_price: float, prices: List[List[float]], days: int
    ) -> float:
        """
        Calculate percentage change for a given period for crypto.

        Args:
            current_price: Current price
            prices: List of [timestamp, price] pairs
            days: Number of days to look back

        Returns:
            Percentage change, or None if data is insufficient
        """
        if not prices:
            return None

        # Find the price closest to the target date
        current_time = datetime.now().timestamp() * 1000  # CoinGecko uses milliseconds
        target_time = current_time - (days * 24 * 60 * 60 * 1000)

        closest_price = None
        closest_diff = float("inf")

        for timestamp, price in prices:
            if price is None:
                continue

            diff = abs(timestamp - target_time)
            if diff < closest_diff:
                closest_diff = diff
                closest_price = price

        if closest_price and closest_price > 0:
            return ((current_price - closest_price) / closest_price) * 100

        return None

    def _calculate_crypto_ytd_change(
        self, current_price: float, prices: List[List[float]]
    ) -> float:
        """
        Calculate year-to-date percentage change for crypto.

        Args:
            current_price: Current price
            prices: List of [timestamp, price] pairs

        Returns:
            YTD percentage change, or None if data is insufficient
        """
        if not prices:
            return None

        # Find the first price of the current year
        current_year = datetime.now().year
        year_start = datetime(current_year, 1, 1).timestamp() * 1000  # CoinGecko uses milliseconds

        year_start_price = None
        for timestamp, price in prices:
            if price is None:
                continue

            if timestamp >= year_start:
                year_start_price = price
                break

        if year_start_price and year_start_price > 0:
            return ((current_price - year_start_price) / year_start_price) * 100

        return None

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform market data to widget format.

        Args:
            raw_data: Raw market data

        Returns:
            Transformed market data
        """
        return raw_data
