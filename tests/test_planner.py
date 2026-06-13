from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.planner import PlannerAgent
from src.events.market_signal import AssetPrice, MarketSnapshot
from src.models.trading import TradeAction, TradeDirection, TradePlan


@pytest.mark.asyncio
async def test_planner_agent_plan():
    # Mock MarketSnapshot
    snapshot = MarketSnapshot(source="binance", assets={"SOL": AssetPrice(price=150.0)})
    balances = {"solana": {"usdc": 200.0, "native": 1.0}}

    # Mock PlannerAgent to avoid needing a real GROQ_API_KEY
    with (
        patch("os.getenv", return_value="dummy_key"),
        patch("src.agents.planner.ChatGroq"),
        patch("src.agents.planner.PLANNER_PROMPT_TEMPLATE") as mock_prompt,
    ):
        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain

        agent = PlannerAgent(model_name="test-model")

        # Configure the mock chain's ainvoke method to return the TradePlan
        mock_chain.ainvoke = AsyncMock(
            return_value=TradePlan(
                actions=[
                    TradeAction(
                        chain="solana",
                        direction=TradeDirection.BUY,
                        amount=10.0,
                        asset="SOL",
                    )
                ],
                rationale="test",
                risk_level="low",
            )
        )

        # Ensure the agent's internal attribute points to our mock chain
        agent.structured_llm = mock_chain

        plan = await agent.plan(snapshot, balances)

        assert len(plan.actions) == 1
        assert plan.actions[0].asset == "SOL"
        assert plan.rationale == "test"
