"""Market information widget implementation."""
import aiohttp
import logging
from typing import Dict, Any, List
from app.widgets.base_widget import BaseWidget

logger = logging.getLogger(__name__)


class MarketWidget(BaseWidget):
    """Widget for displaying market information (stocks, indices, crypto)."""

    widget_type = "market"

    def validate_config(self) -> bool:
        """Validate market widget configuration."""
        # At least one of stocks or crypto must be configured
        has_stocks = "stocks" in self.config and isinstance(self.config["stocks"], list)
        has_crypto = "crypto" in self.config and isinstance(self.config["crypto"], list)

        if not has_stocks and not has_crypto:
            logger.error("Market widget must have either 'stocks' or 'crypto' configured")
            return False

        return True

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch market data from Yahoo Finance API (free, no key required).

        Returns:
            Dictionary containing market data
        """
        stocks = self.config.get("stocks", [])
        crypto = self.config.get("crypto", [])

        result = {
            "stocks": [],
            "crypto": []
        }

        # Fetch stock data
        if stocks:
            stock_data = await self._fetch_yahoo_finance(stocks)
            result["stocks"] = stock_data

        # Fetch crypto data (using Coinbase API - free, no key)
        if crypto:
            crypto_data = await self._fetch_crypto_data(crypto)
            result["crypto"] = crypto_data

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

        async with aiohttp.ClientSession() as session:
            for symbol in symbols:
                try:
                    url = f"{base_url}/{symbol}"
                    params = {
                        "interval": "1d",
                        "range": "5d"  # Get 5 days for trend calculation
                    }

                    async with session.get(url, params=params) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch {symbol}: {response.status}")
                            continue

                        data = await response.json()

                        # Extract relevant data
                        chart = data.get("chart", {})
                        result = chart.get("result", [])

                        if not result:
                            logger.warning(f"No data for symbol {symbol}")
                            continue

                        quote_data = result[0]
                        meta = quote_data.get("meta", {})
                        indicators = quote_data.get("indicators", {})
                        quote = indicators.get("quote", [{}])[0]

                        # Get current price
                        current_price = meta.get("regularMarketPrice")
                        previous_close = meta.get("previousClose")

                        if current_price is None:
                            logger.warning(f"No price data for {symbol}")
                            continue

                        # Calculate change
                        change = None
                        change_percent = None
                        if previous_close:
                            change = current_price - previous_close
                            change_percent = (change / previous_close) * 100

                        results.append({
                            "symbol": symbol,
                            "name": meta.get("longName") or meta.get("shortName") or symbol,
                            "price": round(current_price, 2),
                            "change": round(change, 2) if change else None,
                            "change_percent": round(change_percent, 2) if change_percent else None,
                            "currency": meta.get("currency", "USD"),
                            "market_state": meta.get("marketState", "REGULAR")
                        })

                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {str(e)}")
                    continue

        return results

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
            "XRP": "ripple"
        }

        # Convert symbols to IDs
        crypto_ids = []
        for symbol in symbols:
            symbol_upper = symbol.upper()
            if symbol_upper in symbol_map:
                crypto_ids.append(symbol_map[symbol_upper])
            else:
                # Try to use as lowercase ID directly
                crypto_ids.append(symbol.lower())

        if not crypto_ids:
            return results

        # CoinGecko API endpoint
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"CoinGecko API error: {response.status}")
                        return results

                    data = await response.json()

                    # Build results
                    for symbol, crypto_id in zip(symbols, crypto_ids):
                        if crypto_id in data:
                            crypto_data = data[crypto_id]
                            price = crypto_data.get("usd")
                            change_24h = crypto_data.get("usd_24h_change")

                            if price is not None:
                                results.append({
                                    "symbol": symbol.upper(),
                                    "name": symbol.upper(),
                                    "price": round(price, 2) if price >= 1 else round(price, 6),
                                    "change": None,  # Not directly available
                                    "change_percent": round(change_24h, 2) if change_24h else None,
                                    "currency": "USD",
                                    "market_state": "24/7"
                                })
                        else:
                            logger.warning(f"No data for crypto {symbol}")

        except Exception as e:
            logger.error(f"Error fetching crypto data: {str(e)}")

        return results

    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform market data to widget format.

        Args:
            raw_data: Raw market data

        Returns:
            Transformed market data
        """
        return raw_data
