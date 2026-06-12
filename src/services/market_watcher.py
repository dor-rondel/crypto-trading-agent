"""
Orchestrator for polling market data and emitting batched snapshots.
"""

import asyncio
import logging
from typing import Awaitable, Callable, List, Optional

from src.events.market_signal import MarketSnapshot
from src.services.market_data.base_provider import BaseMarketProvider
from src.services.market_data.coingecko_provider import CoinGeckoProvider

logger = logging.getLogger(__name__)


class MarketWatcher:
    """
    Polls market data providers at regular intervals and emits snapshots.
    """

    def __init__(
        self,
        assets: List[str],
        interval: int = 45,
        providers: Optional[List[BaseMarketProvider]] = None,
    ) -> None:
        """
        Initialize the MarketWatcher.

        Args:
            assets: List of assets to watch.
            interval: Polling interval in seconds.
            providers: List of market data providers. Defaults to CoinGeckoProvider.
        """
        self.assets = assets
        self.interval = interval
        self.providers = providers or [CoinGeckoProvider()]
        self._is_running = False
        self._callback: Optional[Callable[[MarketSnapshot], Awaitable[None]]] = None

    def on_snapshot(
        self, callback: Callable[[MarketSnapshot], Awaitable[None]]
    ) -> None:
        """
        Registers an async callback to be executed when a snapshot is detected.
        """
        self._callback = callback

    async def start(self) -> None:
        """
        Starts the polling loop.
        """
        if self._is_running:
            logger.warning("MarketWatcher is already running.")
            return

        self._is_running = True
        logger.info(
            "Starting MarketWatcher (Batched) with interval=%ds for assets=%s",
            self.interval,
            self.assets,
        )

        try:
            while self._is_running:
                logger.debug("Polling market snapshots from all providers...")

                all_assets = {}
                sources = []

                # Gather snapshots from all providers
                for provider in self.providers:
                    try:
                        snapshot = await provider.get_snapshot(self.assets)
                        if snapshot:
                            all_assets.update(snapshot.assets)
                            sources.append(snapshot.source)
                    except Exception as e:
                        logger.error(
                            "Error polling from %s: %s", type(provider).__name__, e
                        )

                # Emit a single batched snapshot if data was received
                if all_assets and self._callback:
                    batched_snapshot = MarketSnapshot(
                        assets=all_assets,
                        source=", ".join(sources),
                    )
                    logger.info(
                        "Triggering agent with batched snapshot from %s (%d assets)",
                        batched_snapshot.source,
                        len(batched_snapshot.assets),
                    )
                    await self._callback(batched_snapshot)

                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.info("MarketWatcher polling cancelled.")
        except Exception as e:
            logger.error("Unexpected error in MarketWatcher: %s", e)
        finally:
            self._is_running = False
            logger.info("MarketWatcher stopped.")

    def stop(self) -> None:
        """
        Stops the polling loop.
        """
        self._is_running = False
