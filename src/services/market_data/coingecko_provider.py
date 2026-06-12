"""
CoinGecko implementation of the market data provider.
"""

import logging
from typing import Dict, List, Optional

import httpx

from src.events.market_signal import AssetPrice, MarketSnapshot
from src.services.market_data.base_provider import BaseMarketProvider

logger = logging.getLogger(__name__)


class CoinGeckoProvider(BaseMarketProvider):
    """
    Fetches market data from the CoinGecko Public API.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Map internal symbols to CoinGecko IDs
    SYMBOL_MAP = {
        "ETH": "ethereum",
        "SOL": "solana",
        "AVAX": "avalanche-2",
        "USDC": "usd-coin",
    }

    async def get_snapshot(self, assets: List[str]) -> Optional[MarketSnapshot]:
        """
        Fetches current prices from CoinGecko and returns a MarketSnapshot.
        """
        cg_ids = [
            self.SYMBOL_MAP[a.upper()] for a in assets if a.upper() in self.SYMBOL_MAP
        ]

        if not cg_ids:
            logger.warning("No valid CoinGecko IDs found for assets: %s", assets)
            return None

        ids_param = ",".join(cg_ids)
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ids_param,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            asset_prices: Dict[str, AssetPrice] = {}
            # Reverse map to get symbols back from IDs
            id_to_symbol = {v: k for k, v in self.SYMBOL_MAP.items()}

            for cg_id, prices in data.items():
                symbol = id_to_symbol.get(cg_id)
                if symbol:
                    asset_prices[symbol] = AssetPrice(
                        price=float(prices["usd"]),
                        change_24h=float(prices.get("usd_24h_change", 0.0)),
                    )

            if not asset_prices:
                return None

            return MarketSnapshot(assets=asset_prices, source="CoinGecko")

        except Exception as e:
            logger.error("Failed to fetch snapshot from CoinGecko: %s", e)
            return None
