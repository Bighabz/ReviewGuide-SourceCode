"""
Product Compose Tool

Formats final product response with UI blocks and citations.
"""

import sys
import os
import json
from typing import Dict, Any, List
from app.core.error_manager import tool_error_handler

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Tool contract for planner
TOOL_CONTRACT = {
    "name": "product_compose",
    "intent": "product",
    "purpose": "Generate final response with product carousel, recommendations, and comparison table. Formats all product data into UI-ready response. This is the final tool in the product flow.",
    "tools": {
        "pre": [],  # Auto-added at end of product intent
        "post": []
    },
    "produces": ["assistant_text", "ui_blocks", "citations"],
    "citation_message": "Creating recommendations...",
    "tool_order": 800,
    "is_default": True,
    "is_required": True
}

# Provider display configuration - add new providers here
PROVIDER_CONFIG = {
    "ebay": {
        "title": "Shop on eBay",
        "type": "ebay_products",
        "order": 1
    },
    "amazon": {
        "title": "Shop on Amazon",
        "type": "amazon_products",
        "order": 2
    },
    # Add more providers here as needed:
    # "walmart": {"title": "Shop on Walmart", "type": "walmart_products", "order": 3},
}


@tool_error_handler(tool_name="product_compose", error_message="Failed to compose product response")
async def product_compose(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format final product response with assistant text and UI blocks.

    Reads from state:
        - user_message: Original user query
        - normalized_products: Normalized product data
        - affiliate_products: Dict of provider -> products (dynamic)
        - intent: User intent (optional)
        - slots: Extracted slots (optional)

    Writes to state:
        - assistant_text: Final response text
        - ui_blocks: UI components for display (dynamic provider carousels + recommendations)
        - citations: Source citations

    Returns:
        {
            "assistant_text": str,
            "ui_blocks": [...],
            "citations": [...],
            "success": bool
        }
    """
    # Import here to avoid settings validation at module load
    from app.core.centralized_logger import get_logger
    from app.services.model_service import model_service
    from app.core.config import settings

    logger = get_logger(__name__)

    try:
        # Read from state
        user_message = state.get("user_message", "")
        normalized_products = state.get("normalized_products", [])
        affiliate_products = state.get("affiliate_products", {})  # Dynamic: {"ebay": [...], "amazon": [...]}
        intent = state.get("intent", "product")
        slots = state.get("slots")
        comparison_table = state.get("comparison_table")

        # Log provider info
        providers_with_data = list(affiliate_products.keys())
        logger.info(f"[product_compose] Composing response for {len(normalized_products)} products with providers: {providers_with_data}")

        # Check for comparison HTML from product_comparison tool
        comparison_html = state.get("comparison_html")
        comparison_data = state.get("comparison_data")

        # Check if we have any data to display
        if not normalized_products and not affiliate_products:
            return {
                "assistant_text": "I couldn't find any products matching your criteria.",
                "ui_blocks": [],
                "citations": [],
                "success": True
            }

        # Merge affiliate links into products for UI display
        # Flatten all affiliate offers from all providers for matching
        all_affiliate_groups = []
        for provider_name, provider_groups in affiliate_products.items():
            for group in provider_groups:
                all_affiliate_groups.append({
                    **group,
                    "provider": provider_name
                })

        products_with_offers = []
        for product in normalized_products:
            product_copy = product.copy()
            product_name = product.get('name', '')

            # Find matching affiliate links by product name from any provider
            matching_affiliate = next(
                (a for a in all_affiliate_groups if product_name in a.get("product_name", "")),
                None
            )

            if matching_affiliate and matching_affiliate.get("offers"):
                best_offer = matching_affiliate["offers"][0]  # First/best offer
                product_copy["best_offer"] = {
                    "merchant": best_offer.get("merchant", ""),
                    "price": best_offer.get("price", 0),
                    "currency": best_offer.get("currency", "USD"),
                    "url": best_offer.get("url", ""),
                    "image_url": best_offer.get("image_url", ""),
                    "rating": best_offer.get("rating"),
                    "review_count": best_offer.get("review_count"),
                    "source": matching_affiliate.get("provider", "")
                }

            products_with_offers.append(product_copy)

        # Generate descriptions in parallel for each product
        import asyncio

        async def generate_product_description(product: Dict[str, Any], rank: int) -> str:
            """Generate description for a single product."""
            pros = product.get("pros", [])
            pros_text = ", ".join(pros[:3]) if pros else "N/A"

            prompt = f"""Product: {product.get("name", "")}
Summary: {product.get("snippet", "")[:150]}
Key Features: {pros_text}

Write 1-2 concise sentences highlighting:
- The product name with key specs
- What makes it stand out (e.g., "Best overall", "Best for budget", "Best value")

Format: **Product Name**
Description here."""

            description = await model_service.generate(
                messages=[
                    {"role": "system", "content": "You are a product expert. Write concise, compelling product descriptions."},
                    {"role": "user", "content": prompt}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=80,  # Just 1-2 sentences per product
                agent_name="product_compose"
            )
            return description.strip()

        # Generate intro and all product descriptions in parallel
        async def generate_intro() -> str:
            """Generate brief intro."""
            intro_prompt = f'User asked: "{user_message}". Write ONE brief sentence (max 15 words) acknowledging the request.'
            return await model_service.generate(
                messages=[
                    {"role": "system", "content": "You are helpful and concise."},
                    {"role": "user", "content": intro_prompt}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=30,
                agent_name="product_compose"
            )

        # Run intro + all product descriptions in parallel
        tasks = [generate_intro()]
        for idx, product in enumerate(products_with_offers[:8], 1):  # Top 8 products
            tasks.append(generate_product_description(product, idx))

        results = await asyncio.gather(*tasks)

        # Combine results
        intro = results[0].strip()
        product_descriptions = results[1:]

        # Build final response
        if comparison_html:
            # Comparison mode - show intro before comparison table
            product_names = comparison_data.get("products", []) if comparison_data else []
            assistant_text = f"## Product Comparison: {', '.join(product_names)}\n\nHere's a detailed specification comparison."
        elif product_descriptions:
            assistant_text = f"{intro}\n\n## Top Recommendations\n\n"
            assistant_text += "\n\n".join(product_descriptions)
        else:
            # No normalized products, but we may have affiliate products to show
            assistant_text = f"{intro}\n\nHere are some products from our partners:"

        # Create UI blocks dynamically based on available providers
        ui_blocks = []

        # Add comparison HTML if exists (from product_comparison tool)
        if comparison_html:
            ui_blocks.append({
                "type": "comparison_html",
                "title": "Product Comparison",
                "data": {
                    "html": comparison_html,
                    "products": comparison_data.get("products", []) if comparison_data else []
                }
            })
            logger.info(f"[product_compose] Added comparison HTML block ({len(comparison_html)} chars)")

        # Build provider carousels dynamically
        # Sort providers by their configured order
        sorted_providers = sorted(
            affiliate_products.keys(),
            key=lambda p: PROVIDER_CONFIG.get(p, {}).get("order", 999)
        )

        for provider_name in sorted_providers:
            provider_data = affiliate_products.get(provider_name, [])
            if not provider_data:
                continue

            # Get provider config or create default
            config = PROVIDER_CONFIG.get(provider_name, {
                "title": f"Shop on {provider_name.title()}",
                "type": f"{provider_name}_products",
                "order": 999
            })

            # Extract products from provider data
            provider_products = []
            for affiliate_group in provider_data:
                if affiliate_group.get("offers"):
                    for offer in affiliate_group["offers"][:3]:  # Top 3 offers per product
                        product_item = {
                            "title": offer.get("title", ""),
                            "price": offer.get("price", 0),
                            "currency": offer.get("currency", "USD"),
                            "url": offer.get("url", ""),
                            "image_url": offer.get("image_url", ""),
                            "merchant": offer.get("merchant", provider_name.title()),
                            "rating": offer.get("rating"),
                            "review_count": offer.get("review_count"),
                            "source": provider_name
                        }
                        # Include product_id if present (e.g., ASIN for Amazon)
                        if offer.get("product_id"):
                            product_item["product_id"] = offer["product_id"]
                        provider_products.append(product_item)

            if provider_products:
                ui_blocks.append({
                    "type": config["type"],
                    "title": config["title"],
                    "data": provider_products[:10]  # Limit to 10 products
                })
                logger.info(f"[product_compose] Added {len(provider_products)} {provider_name} products to UI")

        # Create citations
        citations = [p["url"] for p in normalized_products if p.get("url")][:5]

        # Log summary
        provider_summary = ", ".join([f"{len(affiliate_products.get(p, []))} {p}" for p in sorted_providers])
        logger.info(f"[product_compose] Generated response: {len(assistant_text)} chars, providers: {provider_summary}")

        return {
            "assistant_text": assistant_text,
            "ui_blocks": ui_blocks,
            "citations": citations,
            "success": True
        }

    except Exception as e:
        logger.error(f"[product_compose] Error: {e}", exc_info=True)

        return {
            "assistant_text": "I encountered an error while formatting the response.",
            "ui_blocks": [],
            "citations": [],
            "error": str(e),
            "success": False
        }
