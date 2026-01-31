# backend/app/services/langgraph/nodes/routing_gate.py
"""Routing Gate Node - Decides between tiered routing and LLM planner."""

from typing import Dict, Any

# Intents that use deterministic tiered routing
DETERMINISTIC_INTENTS = {
    "product",
    "comparison",
    "price_check",
    "travel",
    "review_deep_dive",
}


async def routing_gate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Decide whether to use tiered routing or LLM planner.

    Routes product/travel/price/comparison intents to deterministic
    tiered routing. Routes general/unclear/intro intents to LLM planner.

    Args:
        state: GraphState with intent field set

    Returns:
        Updated state with routing_mode and next_agent
    """
    intent = state.get("intent", "unclear")

    if intent in DETERMINISTIC_INTENTS:
        return {
            **state,
            "routing_mode": "tiered",
            "next_agent": "tiered_executor",
        }
    else:
        return {
            **state,
            "routing_mode": "llm",
            "next_agent": "planner",
        }
