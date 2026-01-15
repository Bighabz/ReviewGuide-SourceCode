"""
Unclear Compose Tool

Generates a friendly message asking user to enter meaningful text when gibberish/unclear input is detected.
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
    "name": "unclear_compose",
    "intent": "unclear",
    "purpose": "Generate a friendly message asking user to enter meaningful text",
    "tools": {
        "pre": [],
        "post": []
    },
    "produces": ["assistant_text"],
    "tool_order": 800,
    "is_default": True,
    "is_required": True
}


@tool_error_handler(tool_name="unclear_compose", error_message="Failed to compose unclear response")
async def unclear_compose(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a friendly clarification message when user input is unclear/gibberish.

    Args:
        state: State dict (no specific inputs required)

    Returns:
        {
            "success": bool,
            "assistant_text": str  # Friendly message asking for meaningful input
        }
    """
    try:
        logger.info("Generating unclear input response...")

        user_message = state.get("user_message", "")

        prompt = f"""The user entered something that appears to be gibberish or unclear text: "{user_message}"

Generate a short, friendly message that:
1. Acknowledges we didn't understand their input
2. Politely asks them to rephrase or enter a meaningful question
3. Optionally gives 1-2 example questions they could ask

Keep it brief (2-3 sentences max), warm, and helpful. Don't be condescending."""

        response = await model_service.generate(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=settings.COMPOSER_MODEL,
            temperature=0.7,
            max_tokens=150,
            agent_name="unclear"
        )

        logger.info("Unclear response generated successfully")

        return {
            "success": True,
            "assistant_text": response
        }

    except Exception as e:
        logger.error(f"Error generating unclear response: {str(e)}", exc_info=True)
        # Fallback message
        return {
            "success": True,
            "assistant_text": "I didn't quite catch that. Could you please rephrase your question? For example, you could ask about travel destinations, product recommendations, or general information."
        }
