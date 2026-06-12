# pylint: disable=fixme

"""
Main workflow entry point for the crypto trading agent.
Initializes services and orchestrates the Plan → Validate → Execute flow.
"""

import asyncio
import logging
from typing import Annotated, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.events.market_signal import MarketSnapshot
from src.monitoring.logging_config import setup_logging
from src.services.market_watcher import MarketWatcher
from src.services.wallet_manager import WalletManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    Represents the state of the agent workflow.
    """

    messages: Annotated[list[str], "The messages in the conversation"]
    portfolio_balances: Dict[str, Dict[str, float]]
    market_snapshot: Optional[MarketSnapshot]
    next_step: str


def planner(state: AgentState) -> AgentState:
    """
    Plan the next trading action based on market signals and portfolio state.
    """
    snapshot = state.get("market_snapshot")
    if snapshot:
        assets_info = ", ".join(
            [f"{a}: ${p.price:.2f}" for a, p in snapshot.assets.items()]
        )
        print(f"\n[PLANNER] Analyzing snapshot: {assets_info}")
    else:
        print("\n[PLANNER] No market data provided.")

    # TODO: Integrate Groq for LLM planning # noqa
    state["next_step"] = "validator"
    return state


def validator(state: AgentState) -> AgentState:
    """
    Validate the proposed plan against deterministic constraints.
    """
    print("[VALIDATOR] Validating plan constraints...")
    # pylint: disable=all
    # TODO: Implement deterministic validation
    # pylint: enable=all
    state["next_step"] = "executor"
    return state


def executor(state: AgentState) -> AgentState:
    """
    Execute the validated plan using chain-specific adapters.
    """
    print("[EXECUTOR] Executing trade actions...")
    # TODO: Implement execution logic
    state["next_step"] = END
    return state


async def wait_for_funding(wm: WalletManager) -> Dict[str, Dict[str, float]]:
    """
    Polls for balances until funds are detected.
    """
    logger.info("Checking for funds...")
    while True:
        current_balances = await wm.get_balances()
        has_funds = False

        print("\n--- Current Portfolio Status ---")
        for network, assets in current_balances.items():
            print(
                f"[{network.upper()}] Native: {assets['native']:.4f} | "
                f"USDC: {assets['usdc']:.2f}"
            )
            if assets["native"] > 0 or assets["usdc"] > 0:
                has_funds = True

        if has_funds:
            logger.info("Funds detected! Proceeding to Stage 2 (Market Polling).")
            return current_balances

        logger.info("No funds detected. Retrying in 30 seconds...")
        await asyncio.sleep(30)


# Define the graph
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner)
workflow.add_node("validator", validator)
workflow.add_node("executor", executor)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "validator")
workflow.add_edge("validator", "executor")
workflow.add_edge("executor", END)

app = workflow.compile()


async def main() -> None:
    """
    Main entry point.
    """
    print("🚀 Initializing Crypto Trading Agent...")

    # Initialize Wallet Manager
    wm_instance = WalletManager()
    await wm_instance.initialize()

    # Stage 1: Wait for funds
    await wait_for_funding(wm_instance)

    # Stage 2: Start Market Watcher
    watcher = MarketWatcher(assets=["ETH", "SOL", "AVAX"], interval=45)

    async def handle_snapshot(snapshot: MarketSnapshot) -> None:
        """
        Callback to trigger the workflow on new market snapshots.
        """
        print(f"\n🔔 New Market Snapshot from {snapshot.source}")
        await app.ainvoke(
            {
                "messages": ["New market data received"],
                "portfolio_balances": await wm_instance.get_balances(),
                "market_snapshot": snapshot,
                "next_step": "",
            }
        )

    watcher.on_snapshot(handle_snapshot)

    # Run the watcher loop
    await watcher.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Gracefully shutting down...")
