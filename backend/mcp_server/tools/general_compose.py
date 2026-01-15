"""
General Compose Tool

Generates final response for general information queries (NOT product recommendations).
For intent="general" - factual answers based on search results.
"""

from app.core.centralized_logger import get_logger
from app.core.error_manager import tool_error_handler
import sys
import os
from typing import Dict, Any
from app.core.error_manager import tool_error_handler

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.model_service import model_service
from app.core.config import settings

logger = get_logger(__name__)

# Tool contract for planner
TOOL_CONTRACT = {
    "name": "general_compose",
    "intent": "general",
    "purpose": "Generate final text response for general information queries (intent=general ONLY, NOT for product recommendations). This is the final tool in the general intent flow.",
    "tools": {
        "pre": [],  # Auto-added at end of general intent
        "post": []
    },
    "produces": ["assistant_text", "ui_blocks", "citations"],
    "citation_message": "Writing answer...",
    "tool_order": 800,
    "is_default": True,
    "is_required": True
}


@tool_error_handler(tool_name="general_compose", error_message="Failed to compose general response")
async def general_compose(
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compose final response for general queries.

    Reads from state:
        - user_message: User's question
        - search_results: Search results from general_search

    Writes to state:
        - assistant_text: Final response text
        - ui_blocks: UI blocks (empty for general queries)
        - citations: Source citations

    Returns:
        {
            "assistant_text": str,
            "ui_blocks": [],
            "citations": [],
            "success": bool
        }
    """
    try:
        user_message = state.get("user_message", "")
        search_results = state.get("search_results", [])

        logger.info(f"[general_compose] Composing response for: {user_message}")

        if not search_results:
            return {
                "assistant_text": "I couldn't find any information about that. Could you rephrase your question?",
                "ui_blocks": [],
                "citations": [],
                "success": True
            }

        # Build context from search results
        context = ""
        for idx, result in enumerate(search_results[:5], 1):
            context += f"[{idx}] {result.get('title', '')}\n{result.get('snippet', '')}\n\n"

        # Generate response using LLM
        prompt = f"""User asked: "{user_message}"

Based on these search results, provide a clear, accurate answer:

{context}

Answer the user's question directly and concisely. Use citation markers [1], [2], etc. when referencing sources."""

        # Callbacks are automatically inherited from LangGraph context
        assistant_text = await model_service.generate(
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Provide accurate, well-sourced answers to questions."},
                {"role": "user", "content": prompt}
            ],
            model=settings.COMPOSER_MODEL,
            temperature=0.7,
            max_tokens=500,
            agent_name="general_compose"
        )

        # Extract citations
        citations = [r.get("url", "") for r in search_results[:5]]

        logger.info(f"[general_compose] Generated response: {len(assistant_text)} chars")

        return {
            "assistant_text": assistant_text,
            "ui_blocks": [],  # No special UI blocks for general queries
            "citations": citations,
            "success": True
        }

    except Exception as e:
        logger.error(f"[general_compose] Error: {e}", exc_info=True)
        return {
            "assistant_text": "I encountered an error generating the response. Please try again.",
            "ui_blocks": [],
            "citations": [],
            "error": str(e),
            "success": False
        }
