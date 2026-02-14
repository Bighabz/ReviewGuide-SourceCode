"""
Product Ranking Tool

Ranks products by quality, relevance, and user preferences.
"""

from app.core.centralized_logger import get_logger
from app.core.error_manager import tool_error_handler
import sys
import os
from typing import Dict, Any, List
from app.core.error_manager import tool_error_handler

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

logger = get_logger(__name__)

# Tool contract for planner
TOOL_CONTRACT = {
    "name": "product_ranking",
    "intent": "product",
    "purpose": "Scores and ranks products based on multiple quality factors including review sentiment, ratings, value for money, and relevance to user criteria. This tool combines evidence from reviews with search relevance to produce an ordered list from best to worst. Use this when user wants to know which product is best overall or needs help prioritizing between multiple options.",
    "tools": {
        "pre": [],  # Needs review_aspects from evidence
        "post": []  # Compose is auto-added at end of intent
    },
    "produces": ["ranked_products"],
    "citation_message": "Ranking by quality and value...",
    "is_default": True
}


@tool_error_handler(tool_name="product_ranking", error_message="Failed to rank products")
async def product_ranking(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rank products by quality and relevance.

    Reads from state:
        - search_results: Products to rank
        - review_aspects: Review analysis results (optional)
        - affiliate_links: Affiliate link data (optional)
        - user_profile: User preferences (optional)

    Writes to state:
        - ranked_products: Ranked list of products with scores

    Returns:
        {
            "ranked_items": [...],
            "success": bool
        }
    """
    try:
        # Read from state
        products = state.get("search_results", [])
        review_aspects = state.get("review_aspects")
        affiliate_links = state.get("affiliate_links")
        user_profile = state.get("user_profile")

        logger.info(f"[product_ranking] Ranking {len(products)} products")

        ranked_items = []

        for idx, product in enumerate(products):
            product_name = product.get("title") or product.get("name", f"Product {idx+1}")

            # Calculate score based on multiple factors
            score = 0.0
            reasons = []

            # Factor 1: Authority score from search
            authority = product.get("authority_score", 0)
            score += authority / 10  # Normalize to 0-1
            if authority > 7:
                reasons.append("High authority source")

            # Factor 2: Review aspects (if available)
            if review_aspects:
                matching_review = next(
                    (r for r in review_aspects if product_name in r.get("product", "")),
                    None
                )
                if matching_review:
                    rating = matching_review.get("rating", 0)
                    score += rating / 5  # Normalize to 0-1
                    if rating >= 4.0:
                        reasons.append(f"Highly rated ({rating}/5)")

                    pros_count = len(matching_review.get("pros", []))
                    if pros_count > 2:
                        reasons.append(f"{pros_count} positive aspects")

            # Factor 3: Affiliate availability
            if affiliate_links:
                has_affiliate = any(
                    product_name in link.get("product_name", "")
                    for link in affiliate_links
                )
                if has_affiliate:
                    score += 0.2
                    reasons.append("Available for purchase")

            # Normalize final score
            score = min(1.0, score)

            ranked_items.append({
                "product_name": product_name,
                "score": round(score, 2),
                "reasons": reasons
            })

        # Sort by score descending
        ranked_items.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"[product_ranking] Top product: {ranked_items[0]['product_name'] if ranked_items else 'None'}")

        return {
            "ranked_items": ranked_items,
            "success": True
        }

    except Exception as e:
        logger.error(f"[product_ranking] Error: {e}", exc_info=True)
        return {
            "ranked_items": [],
            "error": str(e),
            "success": False
        }
