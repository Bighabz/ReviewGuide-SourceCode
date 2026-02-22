"""
Travel General Information Tool

Fallback tool for travel knowledge questions that other specialized tools cannot answer.
Only used when travel_itinerary, travel_destination_facts, travel_search_hotels, travel_search_flights cannot help.
"""

import sys
import os
import json
from typing import Dict, Any
from app.core.error_manager import tool_error_handler

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Tool contract for planner
TOOL_CONTRACT = {
    "name": "travel_general_information",
    "intent": "travel",
    "purpose": "Answer general travel questions",
    "not_for": ["trip planning", "trip itinerary", "destination facts", "hotel search", "flight search", "deals", "plans"],
    "tools": {
        "pre": [],  # Entry-point tool - no dependencies
        "post": []  # Compose is auto-added at end of intent
    },
    "produces": ["general_travel_info"],
    "citation_message": "Searching for travel information...",
    "tool_order": 150  # Lower priority - fallback tool
}


@tool_error_handler(tool_name="travel_general_information", error_message="Failed to search travel information")
async def travel_general_information(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for general travel knowledge using web search.

    Reads from state:
        - user_message: User's question
        - slots: Optional structured data

    Writes to state:
        - general_travel_info: Information gathered from search

    Returns:
        {
            "general_travel_info": str,
            "success": bool
        }
    """
    from app.core.centralized_logger import get_logger
    from app.services.model_service import model_service
    from app.core.config import settings

    logger = get_logger(__name__)

    try:
        user_message = state.get("user_message", "")
        slots = state.get("slots", {})
        destination = slots.get("destination", "")

        logger.info(f"[travel_general_information] Searching for: {user_message}")

        # Build search query
        search_query = user_message
        if destination:
            search_query = f"{user_message} {destination}"

        # Fetch real-time web results via Perplexity (if configured)
        web_context = ""
        try:
            from app.services.search.config import get_search_manager
            search_manager = get_search_manager()
            if search_manager:
                search_results = await search_manager.search(
                    query=search_query,
                    intent="travel",
                    max_results=5
                )
                if search_results:
                    from app.services.search.web_context import build_web_context
                    wc = build_web_context(
                        results=search_results,
                        query=search_query,
                        slots=slots,
                    )
                    web_context = wc.text
                    if wc.omitted_count:
                        logger.info(f"[travel_general_information] Web context: {wc.source_count} sources used, {wc.omitted_count} omitted, ~{wc.token_estimate} tokens")
                    logger.info(f"[travel_general_information] Got {len(search_results)} web results")
        except Exception as search_err:
            logger.warning(f"[travel_general_information] Web search failed, continuing with LLM-only: {search_err}")

        # Build prompt for general travel knowledge
        web_section = f"\n\nRecent web results:\n{web_context}\n" if web_context else ""
        knowledge_source = "your knowledge and the web results below" if web_context else "your knowledge"
        prompt = f"""Answer this travel-related question using {knowledge_source}: "{user_message}"
{web_section}
{f"Destination context: {destination}" if destination else ""}

Provide a helpful, accurate answer that explains the concept clearly.
Focus on:
- Visa requirements if asked
- Travel insurance advice if asked
- Packing tips if asked
- General travel procedures if asked
- Airport/transportation info if asked
- Travel regulations if asked

Keep the answer concise (2-3 paragraphs) and helpful.

Return valid JSON:
{{"answer": "Your answer here", "sources": []}}"""

        response = await model_service.generate(
            messages=[
                {"role": "system", "content": "You are a travel knowledge expert. Provide clear, helpful advice about travel logistics, requirements, and procedures."},
                {"role": "user", "content": prompt}
            ],
            model=settings.DEFAULT_MODEL,
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"},
            agent_name="travel_general_information"
        )

        data = json.loads(response)
        answer = data.get("answer", "")

        logger.info(f"[travel_general_information] Generated answer ({len(answer)} chars)")

        return {
            "general_travel_info": answer,
            "success": True
        }

    except Exception as e:
        logger.error(f"[travel_general_information] Error: {e}", exc_info=True)
        return {
            "general_travel_info": "",
            "error": str(e),
            "success": False
        }
