# backend/tests/test_tiered_router/test_routing_gate.py
import pytest
from app.services.langgraph.nodes.routing_gate import routing_gate_node, DETERMINISTIC_INTENTS


@pytest.mark.asyncio
async def test_product_intent_routes_to_tiered():
    """Product intent should route to tiered executor"""
    state = {"intent": "product", "user_message": "best vacuum"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_comparison_intent_routes_to_tiered():
    """Comparison intent should route to tiered executor"""
    state = {"intent": "comparison", "user_message": "dyson vs shark"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_general_intent_routes_to_llm():
    """General intent should route to LLM planner"""
    state = {"intent": "general", "user_message": "what is a vacuum"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


@pytest.mark.asyncio
async def test_unclear_intent_routes_to_llm():
    """Unclear intent should route to LLM planner"""
    state = {"intent": "unclear", "user_message": "hmm"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


def test_deterministic_intents_contains_expected():
    """DETERMINISTIC_INTENTS should contain all expected intents"""
    expected = {"product", "comparison", "price_check", "travel", "review_deep_dive"}
    assert DETERMINISTIC_INTENTS == expected
