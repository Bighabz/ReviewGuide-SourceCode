"""
Intro Compose Tool

Generates and returns introduction/greeting response directly to customer using LLM.
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
    "name": "intro_compose",
    "intent": "intro",
    "purpose": "Generate and return introduction/greeting response to customer",
    "tools": {
        "pre": [],
        "post": []
    },
    "produces": ["assistant_text"],
    "tool_order": 800,
    "is_default": True,
    "is_required": True
}


@tool_error_handler(tool_name="intro_compose", error_message="Failed to compose intro response")
async def intro_compose(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate introduction text and return it directly to customer using LLM.

    Args:
        state: State dict (no specific inputs required)

    Returns:
        {
            "success": bool,
            "assistant_text": str  # Final text to display to customer
        }
    """
    try:
        logger.info("Generating intro response...")

        # Prompt for generating minimal, one-screen introduction
        user_prompt = """Generate a brief, friendly introduction for a smart assistant that helps with product reviews, travel planning, and general information.

Requirements:
- Start with a warm, natural greeting — like texting a knowledgeable friend, not a corporate chatbot
- One sentence describing what you help with
- Include 3 diverse example questions (using bullet points)
- End with an encouraging invitation to ask anything
- Keep it conversational and minimal (one screen only)
- No long explanations or capability lists

Return only the introduction message."""

        # Generate intro using model service
        intro_message = await model_service.generate(
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            model=settings.COMPOSER_MODEL,
            temperature=0.7,
            max_tokens=300,
            agent_name="intro"
        )

        logger.info(f"✅ Intro message generated successfully")

        return {
            "success": True,
            "assistant_text": intro_message
        }

    except Exception as e:
        logger.error(f"Error generating intro: {str(e)}", exc_info=True)
        # Fallback to minimal hardcoded intro
        fallback_message = """Hello 👋
I'm your smart assistant for reviews, product discovery, and trip planning.

Try asking:
• "Best Dyson for pet hair?"
• "Top things to do in Tokyo"
• "Compare iPhone vs Samsung"

Ask anything — I'll guide you."""

        return {
            "success": True,
            "assistant_text": fallback_message
        }
