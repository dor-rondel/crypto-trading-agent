"""
Main workflow entry point for the crypto trading agent.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """
    Represents the state of the agent workflow.
    """

    messages: Annotated[list[str], "The messages in the conversation"]
    next_step: str


def planner(state: AgentState) -> AgentState:
    """
    Plan the next trading action.
    """
    print("Planning...")
    state["next_step"] = "validator"
    return state


def validator(state: AgentState) -> AgentState:
    """
    Validate the proposed plan.
    """
    print("Validating...")
    state["next_step"] = "executor"
    return state


def executor(state: AgentState) -> AgentState:
    """
    Execute the validated plan.
    """
    print("Executing...")
    state["next_step"] = END
    return state


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
    app.invoke({"messages": ["Start trading"], "next_step": ""})
