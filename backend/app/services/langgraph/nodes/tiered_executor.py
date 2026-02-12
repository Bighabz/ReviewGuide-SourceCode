# backend/app/services/langgraph/nodes/tiered_executor.py
"""Tiered Executor Node - Wraps TieredAPIOrchestrator for LangGraph."""

from typing import Dict, Any

from app.services.tiered_router.orchestrator import TieredAPIOrchestrator

# Module-level orchestrator instance
orchestrator = TieredAPIOrchestrator()


async def tiered_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tiered API routing and handle consent flow.

    Wraps TieredAPIOrchestrator.execute() and maps results to
    GraphState fields expected by downstream nodes.

    Args:
        state: GraphState with intent, user_message, user context

    Returns:
        Updated state with:
        - On success/partial: search_results, snippets, sources_used, next_agent="synthesizer"
        - On consent_required: status="halted", halt_reason, consent_prompt, partial_items
    """
    intent = state.get("intent", "product")
    query = state.get("user_message", "")

    result = await orchestrator.execute(intent, query, state)

    if result["status"] == "consent_required":
        # Halt workflow, save state, prompt user
        return {
            **state,
            "status": "halted",
            "halt_reason": "consent_required",
            "consent_prompt": result["consent_prompt"],
            "partial_items": result["items"],
            "partial_snippets": result["snippets"],
            "tier_reached": result["tier_reached"],
            "next_agent": None,  # Wait for user
        }

    # Success or partial - proceed to synthesis
    return {
        **state,
        "tier_results": result,
        "search_results": result["items"],
        "snippets": result["snippets"],
        "sources_used": result["sources_used"],
        "sources_unavailable": result.get("sources_unavailable", []),
        "tier_reached": result["tier_reached"],
        "next_agent": "synthesizer",
    }
