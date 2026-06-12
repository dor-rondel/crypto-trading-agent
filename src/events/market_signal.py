"""
Definitions for market-related events.
"""

from datetime import UTC, datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssetPrice(BaseModel):
    """
    Represents the price data for a single asset.
    """

    price: float = Field(..., description="The current price of the asset in USD")
    change_24h: Optional[float] = Field(
        None, description="24-hour price change percentage"
    )


class MarketSnapshot(BaseModel):
    """
    Represents a batched snapshot of market data.
    """

    model_config = ConfigDict(frozen=True)

    assets: Dict[str, AssetPrice] = Field(
        ..., description="Map of asset symbols to their price data"
    )
    source: str = Field(..., description="The provider that generated this snapshot")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the snapshot",
    )
