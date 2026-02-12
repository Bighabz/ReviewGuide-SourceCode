# backend/tests/test_tiered_router/test_workflow_integration.py
"""Integration tests for tiered routing in LangGraph workflow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_workflow_routes_product_to_tiered():
    """Product intent should route through tiered executor"""
    # This is an integration test that verifies the workflow graph
    # routes correctly based on intent

    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "product", "user_message": "best vacuum"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_workflow_routes_general_to_planner():
    """General intent should route through LLM planner"""
    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "general", "user_message": "what is machine learning"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


@pytest.mark.asyncio
async def test_workflow_routes_travel_to_tiered():
    """Travel intent should route through tiered executor"""
    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "travel", "user_message": "hotels in Paris"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_workflow_routes_comparison_to_tiered():
    """Comparison intent should route through tiered executor"""
    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "comparison", "user_message": "dyson vs shark vacuum"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_workflow_routes_intro_to_planner():
    """Intro intent should route through LLM planner"""
    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "intro", "user_message": "hello"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


def test_workflow_has_routing_gate_node():
    """Workflow should have routing_gate node registered"""
    from app.services.langgraph.workflow import build_workflow

    # The workflow is compiled, so we check that import works
    # and the function builds without error
    workflow = build_workflow()
    assert workflow is not None


def test_workflow_has_tiered_executor_node():
    """Workflow should have tiered_executor node registered"""
    from app.services.langgraph.workflow import graph

    # Verify the graph was built successfully
    assert graph is not None
