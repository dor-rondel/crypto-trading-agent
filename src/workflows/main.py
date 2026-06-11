# pylint: disable=fixme

"""
Main workflow entry point for the crypto trading agent.
Initializes services and orchestrates the Plan → Validate → Execute flow.
"""

import time
from typing import Annotated, Dict, TypedDict

from langgraph.graph import END, StateGraph

from src.services.wallet_manager import WalletManager


class AgentState(TypedDict):
    """
    Represents the state of the agent workflow.
    """

    messages: Annotated[list[str], "The messages in the conversation"]
    portfolio_balances: Dict[str, Dict[str, float]]
    next_step: str


def planner(state: AgentState) -> AgentState:
    """
    Plan the next trading action based on market signals and portfolio state.
    """
    print("Planning...")
    # TODO: Integrate Groq for LLM planning # noqa
    state["next_step"] = "validator"
    return state


def validator(state: AgentState) -> AgentState:
    """
    Validate the proposed plan against deterministic constraints.
    """
    print("Validating...")
    # pylint: disable=all
    # TODO: Implement deterministic validation
    # pylint: enable=all
    state["next_step"] = "executor"
    return state


def executor(state: AgentState) -> AgentState:
    """
    Execute the validated plan using chain-specific adapters.
    """
    print("Executing...")
    # TODO: Implement execution logic
    state["next_step"] = END
    return state


def wait_for_funding(wm: WalletManager) -> Dict[str, Dict[str, float]]:
    """
    Polls for balances until funds are detected.
    """
    print("\n🔍 Checking for funds...")
    while True:
        current_balances = wm.get_balances()
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
            print("\n✅ Funds detected! Proceeding to trading workflow...")
            return current_balances

        print("\n⏳ No funds detected. Please fund your wallets.")
        print("📖 Instructions: Check WALLETS.md for addresses and faucet links.")
        print("🔄 Retrying in 30 seconds...")
        time.sleep(30)


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

if __name__ == "__main__":
    print("🚀 Initializing Crypto Trading Agent...")

    # Initialize Wallet Manager (silently)
    wm_instance = WalletManager()

    # Wait for funds before starting the agentic workflow
    final_balances = wait_for_funding(wm_instance)

    # Start the workflow with initial state
    app.invoke(
        {
            "messages": ["Start trading"],
            "portfolio_balances": final_balances,
            "next_step": "",
        }
    )
