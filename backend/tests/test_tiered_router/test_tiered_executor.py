# backend/tests/test_tiered_router/test_tiered_executor.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.langgraph.nodes.tiered_executor import tiered_executor_node


@pytest.fixture
def mock_state():
    return {
        "intent": "product",
        "user_message": "best vacuum cleaner",
        "user_id": "test-user",
        "session_id": "test-session",
        "user_extended_search_enabled": False,
        "extended_search_confirmed": False,
    }


@pytest.mark.asyncio
async def test_success_sets_search_results(mock_state):
    """Successful execution should set search_results field"""
    mock_result = {
        "status": "success",
        "items": [{"name": "p1"}, {"name": "p2"}, {"name": "p3"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "tier_reached": 1,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["search_results"] == mock_result["items"]
    assert result["next_agent"] == "synthesizer"
    assert result.get("status") != "halted"


@pytest.mark.asyncio
async def test_consent_required_halts_workflow(mock_state):
    """Consent required should halt workflow"""
    mock_result = {
        "status": "consent_required",
        "items": [{"name": "p1"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "consent_prompt": {"type": "per_query", "message": "Search deeper?"},
        "tier_reached": 2,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["status"] == "halted"
    assert result["halt_reason"] == "consent_required"
    assert result["consent_prompt"] == mock_result["consent_prompt"]
    assert result["partial_items"] == mock_result["items"]
    assert result["next_agent"] is None


@pytest.mark.asyncio
async def test_partial_results_proceeds_to_synthesizer(mock_state):
    """Partial results should still proceed to synthesizer"""
    mock_result = {
        "status": "partial",
        "items": [{"name": "p1"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "message": "Showing partial results",
        "tier_reached": 4,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["search_results"] == mock_result["items"]
    assert result["next_agent"] == "synthesizer"
