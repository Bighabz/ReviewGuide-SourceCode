"""
Phase 08 — Clarifier Suggestion Chips: Backend Tests

Tests covering:
  1. Clarifier generates 2-4 chips per follow-up question
  2. Chip text is concise (<= 30 characters)
  3. Fallback questions include chips: [] (never undefined)
  4. GraphState includes clarifier_chips field with default
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_chips_in_followup_response():
    """Clarifier followup questions include a 'chips' key with 2-4 string options."""
    from app.agents.clarifier_agent import ClarifierAgent

    mock_response = json.dumps({
        "intro": "Let me help narrow things down:",
        "questions": [
            {"slot": "budget", "question": "What's your budget range?", "chips": ["Under $100", "$100-$300", "Over $300"]},
            {"slot": "category", "question": "What type of product?", "chips": ["Vacuums", "Hair dryers", "Air purifiers"]}
        ],
        "closing": "I'll find the best options for you!"
    })

    agent = ClarifierAgent.__new__(ClarifierAgent)
    agent.settings = MagicMock()
    agent.settings.CLARIFIER_MODEL = "gpt-4o"
    agent.settings.CLARIFIER_MAX_TOKENS = 500
    agent.generate = AsyncMock(return_value=mock_response)

    result = await agent._generate_followup_questions(
        missing_slots=["budget", "category"],
        current_slots={},
        user_message="I need a Dyson",
        intent="product"
    )

    assert "questions" in result
    assert len(result["questions"]) == 2

    for q in result["questions"]:
        assert "chips" in q, f"Question for slot '{q['slot']}' missing 'chips' key"
        assert isinstance(q["chips"], list)
        assert 2 <= len(q["chips"]) <= 4, f"Expected 2-4 chips, got {len(q['chips'])} for slot '{q['slot']}'"


@pytest.mark.asyncio
async def test_chips_are_short_strings():
    """Each chip text must be <= 30 characters for concise pill-button display."""
    from app.agents.clarifier_agent import ClarifierAgent

    mock_response = json.dumps({
        "intro": "Let me help narrow things down:",
        "questions": [
            {"slot": "budget", "question": "What's your budget range?", "chips": ["Under $100", "$100-$300", "Over $300"]},
            {"slot": "category", "question": "What type of product?", "chips": ["Vacuums", "Hair dryers", "Air purifiers"]}
        ],
        "closing": "I'll find the best options for you!"
    })

    agent = ClarifierAgent.__new__(ClarifierAgent)
    agent.settings = MagicMock()
    agent.settings.CLARIFIER_MODEL = "gpt-4o"
    agent.settings.CLARIFIER_MAX_TOKENS = 500
    agent.generate = AsyncMock(return_value=mock_response)

    result = await agent._generate_followup_questions(
        missing_slots=["budget", "category"],
        current_slots={},
        user_message="I need a Dyson",
        intent="product"
    )

    for q in result["questions"]:
        for chip in q.get("chips", []):
            assert isinstance(chip, str), f"Chip must be a string, got {type(chip)}"
            assert len(chip) <= 30, f"Chip text '{chip}' exceeds 30 chars ({len(chip)})"


@pytest.mark.asyncio
async def test_fallback_questions_include_empty_chips():
    """When LLM call fails, fallback questions must include chips: [] so frontend never receives undefined."""
    from app.agents.clarifier_agent import ClarifierAgent

    agent = ClarifierAgent.__new__(ClarifierAgent)
    agent.settings = MagicMock()
    agent.settings.CLARIFIER_MODEL = "gpt-4o"
    agent.settings.CLARIFIER_MAX_TOKENS = 500
    agent.generate = AsyncMock(side_effect=Exception("LLM call failed"))

    result = await agent._generate_followup_questions(
        missing_slots=["budget", "category"],
        current_slots={},
        user_message="I need a Dyson",
        intent="product"
    )

    assert "questions" in result
    for q in result["questions"]:
        assert "chips" in q, f"Fallback question for slot '{q['slot']}' missing 'chips' key"
        assert q["chips"] == [], f"Fallback chips should be empty list, got {q['chips']}"


def test_graph_state_default():
    """GraphState TypedDict must include clarifier_chips field."""
    from app.schemas.graph_state import GraphState

    assert "clarifier_chips" in GraphState.__annotations__, \
        "GraphState missing 'clarifier_chips' field — must be added to TypedDict"
