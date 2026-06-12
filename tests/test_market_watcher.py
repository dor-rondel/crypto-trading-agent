"""
Tests for the Market Watcher and CoinGecko Provider.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.events.market_signal import MarketSnapshot
from src.services.market_data.coingecko_provider import CoinGeckoProvider
from src.services.market_watcher import MarketWatcher


@pytest.mark.asyncio
async def test_coingecko_provider_success():
    """
    Test successful data fetch from CoinGecko.
    """
    provider = CoinGeckoProvider()
    mock_response = {
        "ethereum": {"usd": 3000.0, "usd_24h_change": -0.5},
        "solana": {"usd": 150.0, "usd_24h_change": 2.0},
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response
        mock_res.raise_for_status = lambda: None
        mock_get.return_value = mock_res

        snapshot = await provider.get_snapshot(["ETH", "SOL"])

    assert snapshot is not None
    assert snapshot.source == "CoinGecko"
    assert "ETH" in snapshot.assets
    assert snapshot.assets["ETH"].price == 3000.0
    assert snapshot.assets["ETH"].change_24h == -0.5
    assert "SOL" in snapshot.assets


@pytest.mark.asyncio
async def test_coingecko_provider_failure():
    """
    Test CoinGeckoProvider handling of API failures and empty data.
    """
    provider = CoinGeckoProvider()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 500
        mock_res.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_res

        snapshot = await provider.get_snapshot(["ETH"])

    assert snapshot is None

    # Empty result
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {}
        mock_res.raise_for_status = lambda: None
        mock_get.return_value = mock_res

        snapshot = await provider.get_snapshot(["ETH"])

    assert snapshot is None


@pytest.mark.asyncio
async def test_market_watcher_polling():
    """
    Test that MarketWatcher correctly polls and emits snapshots.
    """
    mock_provider = AsyncMock()
    from src.events.market_signal import AssetPrice

    mock_snapshot = MarketSnapshot(
        assets={"BTC": AssetPrice(price=50000.0)},
        source="MockProvider",
        timestamp=datetime.now(UTC),
    )
    mock_provider.get_snapshot.return_value = mock_snapshot

    watcher = MarketWatcher(assets=["BTC"], interval=0.1, providers=[mock_provider])

    snapshots_received = []

    async def callback(snapshot):
        snapshots_received.append(snapshot)
        if len(snapshots_received) >= 2:
            watcher.stop()

    watcher.on_snapshot(callback)

    # Run watcher for a short time
    await watcher.start()

    assert len(snapshots_received) >= 2
    assert snapshots_received[0].source == "MockProvider"


@pytest.mark.asyncio
async def test_market_watcher_robustness():
    """
    Test that MarketWatcher handles partial provider failures and skips
    when all providers fail.
    """
    from src.events.market_signal import AssetPrice

    # Provider 1 succeeds, Provider 2 fails
    provider1 = AsyncMock()
    provider1.get_snapshot.return_value = MarketSnapshot(
        assets={"ETH": AssetPrice(price=3000.0)},
        source="GoodProvider",
        timestamp=datetime.now(UTC),
    )

    provider2 = AsyncMock()
    provider2.get_snapshot.side_effect = Exception("API Error")

    watcher = MarketWatcher(
        assets=["ETH"], interval=0.01, providers=[provider1, provider2]
    )

    snapshots_received = []

    async def callback(snapshot):
        snapshots_received.append(snapshot)
        watcher.stop()

    watcher.on_snapshot(callback)

    # Run watcher
    await watcher.start()

    # Should have triggered once with partial data
    assert len(snapshots_received) == 1
    assert "ETH" in snapshots_received[0].assets
    assert snapshots_received[0].source == "GoodProvider"

    # Reset
    snapshots_received = []

    # Both providers fail
    provider1.get_snapshot.side_effect = Exception("API Error 1")
    provider2.get_snapshot.side_effect = Exception("API Error 2")

    watcher._is_running = True  # Reset run flag for retry

    # Run again
    await watcher.start()

    # Callback should not have been triggered
    assert len(snapshots_received) == 0
