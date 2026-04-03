"""
Travel Search Activities Tool

Searches for tours, activities, and experiences via the Viator Partner API.
Returns activity data with names, images, prices, and affiliate booking links.
"""

from app.core.centralized_logger import get_logger
from app.core.error_manager import tool_error_handler
from app.core.config import settings
import sys
import os
import time
from typing import Dict, Any

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.affiliate.providers.viator_provider import ViatorActivityProvider

logger = get_logger(__name__)

# Tool contract for planner
TOOL_CONTRACT = {
    "name": "travel_search_activities",
    "purpose": "Search for tours, activities, experiences, things to do",
    "intent": "travel",
    "tools": {
        "pre": [],   # Entry-point tool - no dependencies
        "post": []    # Compose is auto-added at end of intent
    },
    "produces": ["activities"],
    "required_slots": ["destination"],
    "optional_slots": ["departure_date", "duration_days"],
    "citation_message": "Finding activities and experiences...",
    "tool_order": 100,
    "slot_types": {
        "destination": {"type": "string", "format": "city"},
        "departure_date": {"type": "date", "format": "YYYY-MM-DD"},
        "duration_days": {"type": "integer", "format": "number"},
    }
}


@tool_error_handler(tool_name="travel_search_activities", error_message="Failed to search activities")
async def travel_search_activities(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for tours, activities, and experiences via Viator.

    Reads from state:
        - slots: Contains destination

    Returns:
        {
            "activities": [{
                "type": "activity",
                "provider": "viator",
                "name": str,
                "price_from": float,
                "currency": str,
                "booking_url": str,
                "image_url": str,
                "rating": float,
                "review_count": int,
                "merchant": str
            }],
            "citations": [...],
            "success": bool
        }
    """
    try:
        # Emit streaming status update before executing
        state["stream_chunk_data"] = {
            "type": "tool_citation",
            "data": {"message": "Finding activities..."}
        }
        start = time.monotonic()

        # Read from state
        slots = state.get("slots", {})
        destination = slots.get("destination", "")

        if not destination:
            logger.warning("[travel_search_activities] No destination in slots")
            elapsed = round(time.monotonic() - start, 2)
            return {
                "activities": [],
                "citations": [],
                "error": "No destination provided",
                "tool_timing": {**state.get("tool_timing", {}), "travel_search_activities": elapsed},
                "success": False,
            }

        logger.info(f"[travel_search_activities] Searching activities in: {destination}")

        # Instantiate Viator provider
        provider = ViatorActivityProvider(
            api_key=settings.VIATOR_API_KEY,
            affiliate_id=settings.VIATOR_AFFILIATE_ID,
        )

        # Search for activities
        products = await provider.search_products(
            query=destination,
            limit=settings.VIATOR_MAX_RESULTS,
        )

        # Convert AffiliateProduct to activity dicts for state
        activities = []
        citations = []
        for product in products:
            activity_dict = {
                "type": "activity",
                "provider": "viator",
                "name": product.title,
                "price_from": product.price,
                "currency": product.currency,
                "booking_url": product.affiliate_link,
                "image_url": product.image_url,
                "rating": product.rating,
                "review_count": product.review_count,
                "merchant": product.merchant,
            }
            activities.append(activity_dict)
            if product.affiliate_link:
                citations.append(product.affiliate_link)

        logger.info(f"[travel_search_activities] Found {len(activities)} activities in {destination}")

        elapsed = round(time.monotonic() - start, 2)
        return {
            "activities": activities,
            "citations": citations,
            "tool_timing": {**state.get("tool_timing", {}), "travel_search_activities": elapsed},
            "success": len(activities) > 0,
        }

    except Exception as e:
        logger.error(f"[travel_search_activities] Error: {e}", exc_info=True)
        elapsed = round(time.monotonic() - start, 2)
        return {
            "activities": [],
            "citations": [],
            "error": str(e),
            "tool_timing": {**state.get("tool_timing", {}), "travel_search_activities": elapsed},
            "success": False,
        }
