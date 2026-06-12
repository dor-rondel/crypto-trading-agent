"""
Base interface for market data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.events.market_signal import MarketSnapshot


class BaseMarketProvider(ABC):
    """
    Abstract base class for all market data providers.
    """

    @abstractmethod
    async def get_snapshot(self, assets: List[str]) -> Optional[MarketSnapshot]:
        """
        Fetches current market snapshot for a list of assets.

        Args:
            assets: List of asset symbols (e.g., ["BTC", "ETH"]).

        Returns:
            A MarketSnapshot object or None if fetching failed.
        """
