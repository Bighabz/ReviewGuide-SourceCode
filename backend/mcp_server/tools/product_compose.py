"""
Product Compose Tool

Formats final product response with UI blocks and citations.
"""

import sys
import os
import json
from datetime import datetime
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

# Accessory keywords for relevance filtering
ACCESSORY_KEYWORDS = {
    "case", "charger", "protector", "cable", "adapter",
    "stand", "cover", "sleeve", "mount", "holder", "film",
    "tempered glass", "cleaning kit", "skin", "sticker",
    "screen protector",
}


def _fuzzy_product_match(query_name: str, candidate_name: str, threshold: float = 0.45) -> bool:
    """Token-overlap Jaccard similarity for fuzzy product matching."""
    q_tokens = set(query_name.lower().split())
    c_tokens = set(candidate_name.lower().split())
    if not q_tokens or not c_tokens:
        return False
    intersection = q_tokens & c_tokens
    union = q_tokens | c_tokens
    return len(intersection) / len(union) >= threshold


def _assign_editorial_labels(review_data: dict, products_with_offers: list) -> dict:
    """Assign editorial labels based on review quality + price data.
    Returns {product_name: label} mapping."""
    labels = {}
    if not review_data:
        return labels

    # Best Overall = highest quality_score
    sorted_by_quality = sorted(
        review_data.items(),
        key=lambda x: x[1].get("quality_score", 0),
        reverse=True
    )
    if sorted_by_quality and sorted_by_quality[0][1].get("quality_score", 0) > 0:
        labels[sorted_by_quality[0][0]] = "Best Overall"

    # Budget Pick = lowest priced product that has reviews
    priced_products = []
    for p in products_with_offers:
        offer = p.get("best_offer", {})
        price = offer.get("price", 0) if offer else 0
        name = p.get("name", "")
        if price > 0 and name in review_data:
            priced_products.append((name, price))

    if priced_products:
        cheapest = min(priced_products, key=lambda x: x[1])
        if cheapest[0] not in labels:  # Don't overwrite Best Overall
            labels[cheapest[0]] = "Budget Pick"

    return labels


def _find_price_comparisons(products_by_provider: dict) -> dict:
    """Find products available on multiple retailers and compare prices.
    Returns {product_title_normalized: {"best_retailer": str, "best_price": float, "savings": float, "other_prices": [...]}}"""
    from collections import defaultdict
    price_map = defaultdict(list)

    for provider_name, data in products_by_provider.items():
        for product in data["products"]:
            title = product.get("title", "")
            price = product.get("price", 0)
            if title and price > 0:
                # Use fuzzy matching to group same products
                matched = False
                for key in list(price_map.keys()):
                    if _fuzzy_product_match(title, key, threshold=0.5):
                        price_map[key].append({"retailer": provider_name, "price": price, "title": title})
                        matched = True
                        break
                if not matched:
                    price_map[title].append({"retailer": provider_name, "price": price, "title": title})

    # Only return products found on 2+ retailers
    comparisons = {}
    for key, entries in price_map.items():
        retailers = set(e["retailer"] for e in entries)
        if len(retailers) >= 2:
            sorted_entries = sorted(entries, key=lambda x: x["price"])
            comparisons[key] = {
                "best_retailer": sorted_entries[0]["retailer"],
                "best_price": sorted_entries[0]["price"],
                "savings": round(sorted_entries[-1]["price"] - sorted_entries[0]["price"], 2),
                "other_prices": [{"retailer": e["retailer"], "price": e["price"]} for e in sorted_entries[1:]]
            }

    return comparisons


def _is_follow_up_query(query: str, last_context: dict) -> bool:
    """Detect if query references previous search results."""
    if not last_context:
        return False

    q = query.lower().strip()

    reference_signals = [
        "that one", "the first", "the second", "the third",
        "cheapest", "most expensive", "best rated", "any of",
        "compare them", "which one", "between those",
        "more about", "tell me more", "go back to",
        "the one with", "how about the",
    ]
    if any(signal in q for signal in reference_signals):
        return True

    # Very short query with no product category noun
    if len(q.split()) <= 4:
        return True

    return False


def _find_in_history(query: str, history: list) -> dict | None:
    """Scan search_history for a matching previous context."""
    q = query.lower()
    for ctx in reversed(history):
        cat = ctx.get("category", "").lower()
        ptype = ctx.get("product_type", "").lower()
        if cat and cat in q:
            return ctx
        if ptype and ptype in q:
            return ctx
    return None


def _filter_relevant_products(
    affiliate_products: Dict[str, List],
    user_query: str,
    category: str = None,
) -> Dict[str, List]:
    """
    Filter out accessory products that don't match the user's intent.
    Skips filtering if the user is actually looking for accessories.
    """
    query_lower = user_query.lower()

    # If user is searching for accessories, don't filter
    for kw in ACCESSORY_KEYWORDS:
        if kw in query_lower:
            return affiliate_products

    filtered = {}
    total_before = 0
    total_after = 0

    for provider_name, provider_groups in affiliate_products.items():
        filtered_groups = []
        for group in provider_groups:
            offers = group.get("offers", [])
            total_before += len(offers)

            clean_offers = []
            for offer in offers:
                title_lower = (offer.get("title") or "").lower()
                is_accessory = any(kw in title_lower for kw in ACCESSORY_KEYWORDS)
                if not is_accessory:
                    clean_offers.append(offer)

            total_after += len(clean_offers)

            if clean_offers:
                filtered_groups.append({
                    **group,
                    "offers": clean_offers,
                })

        if filtered_groups:
            filtered[provider_name] = filtered_groups

    removed = total_before - total_after
    if removed > 0:
        from app.core.centralized_logger import get_logger
        get_logger(__name__).info(
            f"[product_compose] Filter: {total_before} → {total_after} products ({removed} filtered)"
        )

    return filtered


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
        affiliate_products_raw = state.get("affiliate_products", {})  # Dynamic: {"ebay": [...], "amazon": [...]}
        intent = state.get("intent", "product")
        slots = state.get("slots")
        last_search_context = state.get("last_search_context", {})
        category = (slots.get("category") if slots else None) or last_search_context.get("category")

        # Filter out accessory junk from any provider
        affiliate_products = _filter_relevant_products(affiliate_products_raw, user_message, category)
        comparison_table = state.get("comparison_table")
        review_data = state.get("review_data", {})  # product_name -> ReviewBundle dict from review_search

        # Log provider info
        providers_with_data = list(affiliate_products.keys())
        logger.info(f"[product_compose] Composing response for {len(normalized_products)} products with providers: {providers_with_data}")

        # Check for comparison HTML from product_comparison tool
        comparison_html = state.get("comparison_html")
        comparison_data = state.get("comparison_data")

        # Check if we have any data to display
        if not normalized_products and not affiliate_products and not review_data:
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
                (a for a in all_affiliate_groups if _fuzzy_product_match(product_name, a.get("product_name", ""))),
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

        # Assign editorial labels based on review quality + price
        editorial_labels = _assign_editorial_labels(review_data, products_with_offers)
        if editorial_labels:
            logger.info(f"[product_compose] Editorial labels: {editorial_labels}")

        # Generate a brief summary - no need for per-product descriptions since cards show the products
        # Build final response (assistant_text set below, may be overridden by review_data block)
        assistant_text = ""
        if comparison_html:
            # Comparison mode - show intro before comparison table
            product_names = comparison_data.get("products", []) if comparison_data else []
            assistant_text = f"## Product Comparison: {', '.join(product_names)}\n\nHere's a detailed specification comparison."
        elif not review_data:
            # No review data — concierge-style summary explaining WHY these match
            total_products = sum(len(p) for p in affiliate_products.values())
            provider_names = [p.title() for p in affiliate_products.keys()]

            conversation_history = state.get("conversation_history", [])
            context_summary = ""
            if conversation_history:
                recent = conversation_history[-4:]
                context_summary = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')[:150]}"
                    for msg in recent if msg.get('content')
                ])

            product_name_list = [p.get("name", "") for p in normalized_products[:5] if p.get("name")]

            assistant_text = await model_service.generate(
                messages=[
                    {"role": "system", "content": "You are a product concierge. Write 2-3 SHORT sentences (max 60 words). Explain WHY these products match the user's needs. Reference their criteria from the conversation (budget, features, use case). Do NOT list products — they are shown in cards below. End with a brief, warm follow-up that shows you remember the user's context. Keep it to one sentence. Reference specific details they mentioned — names, preferences, use cases — to show you're paying attention."},
                    {"role": "user", "content": f'User asked: "{user_message}"\nContext:\n{context_summary}\nProducts: {", ".join(product_name_list)}\nSources: {", ".join(provider_names)}'}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=120,
                agent_name="product_compose"
            )
            assistant_text = assistant_text.strip()
        # else: assistant_text was already built from review_data above

        # Create UI blocks dynamically based on available providers
        ui_blocks = []

        # Add review sources block if review_data exists (from review_search tool)
        if review_data:
            review_products = []
            for product_name, bundle in review_data.items():
                if not bundle.get("sources"):
                    continue

                # Generate consensus summary via LLM
                source_snippets = "\n".join([
                    f"- {s.get('site_name', 'Review')}: {s.get('snippet', '')}"
                    for s in bundle.get("sources", [])[:5]
                ])

                try:
                    consensus = await model_service.generate(
                        messages=[
                            {"role": "system", "content": "You summarize product review consensus. Write 2-3 sentences explaining why this product is highly rated. Mention specific strengths reviewers agree on. Reference source names naturally (e.g., 'According to Wirecutter and RTINGS...'). Be concise and factual."},
                            {"role": "user", "content": f"Product: {product_name}\nAvg Rating: {bundle.get('avg_rating', 0)}/5 from {bundle.get('total_reviews', 0)} reviews\n\nReview excerpts:\n{source_snippets}\n\nWrite a 2-3 sentence consensus summary."}
                        ],
                        model=settings.COMPOSER_MODEL,
                        temperature=0.5,
                        max_tokens=120,
                        agent_name="review_consensus"
                    )
                    consensus = consensus.strip()
                except Exception as consensus_err:
                    logger.warning(f"[product_compose] Failed to generate consensus for {product_name}: {consensus_err}")
                    consensus = ""

                review_products.append({
                    "name": product_name,
                    "avg_rating": bundle.get("avg_rating", 0),
                    "total_reviews": bundle.get("total_reviews", 0),
                    "consensus": consensus,
                    "editorial_label": editorial_labels.get(product_name),
                    "sources": [
                        {
                            "site_name": s.get("site_name", ""),
                            "url": s.get("url", ""),
                            "title": s.get("title", ""),
                            "snippet": s.get("snippet", ""),
                            "rating": s.get("rating"),
                            "favicon_url": s.get("favicon_url", ""),
                            "date": s.get("date"),
                        }
                        for s in bundle.get("sources", [])[:6]
                    ],
                })

            if review_products:
                ui_blocks.append({
                    "type": "review_sources",
                    "title": "What Reviewers Say",
                    "data": {
                        "products": review_products,
                    }
                })

                # Update assistant_text to be review-first
                source_count = sum(len(p["sources"]) for p in review_products)
                assistant_text = f"Based on reviews from {source_count} trusted sources, here's what stands out:\n\n"

                # Add brief per-product highlights
                for rp in review_products[:3]:
                    if rp["consensus"]:
                        assistant_text += f"**{rp['name']}** — {rp['consensus']}\n\n"

                # Add warm closing line
                assistant_text += "Want me to dive deeper into any of these, or compare specific models side-by-side?"

                logger.info(f"[product_compose] Added review_sources block with {len(review_products)} products")

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

        # Collect all products first for description generation
        all_products_for_desc = []
        products_by_provider = {}

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
                        all_products_for_desc.append(product_item)

            if provider_products:
                products_by_provider[provider_name] = {
                    "config": config,
                    "products": provider_products[:10]
                }

        # Generate personalized descriptions for products using conversation context
        if all_products_for_desc:
            products_to_describe = all_products_for_desc[:15]  # Up to 15 products
            product_titles = [p["title"][:50] for p in products_to_describe]

            # Read conversation history for personalization
            conversation_history = state.get("conversation_history", [])

            # Build context summary from recent conversation
            context_summary = ""
            if conversation_history:
                recent_messages = conversation_history[-6:]  # Last 6 messages
                context_summary = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
                    for msg in recent_messages
                    if msg.get('content')
                ])

            # Enhanced prompt for personalized descriptions
            desc_system = """Generate personalized 15-20 word descriptions for each product.

IMPORTANT RULES:
1. If user mentioned a pet name (like "Max", "Bella"), reference it: "Your dog Max would love this because..."
2. If user mentioned a person (girlfriend, baby, mom), personalize: "Perfect gift for your girlfriend..."
3. If no specific context, ask a follow-up question in the description: "Great choice! What breed is your dog?"
4. Vary your descriptions - don't repeat the same pattern
5. Be warm and conversational, not generic

Return JSON: {"descriptions": ["desc1", "desc2", ...]}"""

            desc_user = f'''Conversation context:
{context_summary if context_summary else "No prior context"}

User's current question: "{user_message}"

Products to describe:
{json.dumps(product_titles)}'''

            try:
                desc_response = await model_service.generate(
                    messages=[
                        {"role": "system", "content": desc_system},
                        {"role": "user", "content": desc_user}
                    ],
                    model=settings.COMPOSER_MODEL,
                    temperature=0.7,
                    max_tokens=600,  # Increased for more descriptions
                    response_format={"type": "json_object"},
                    agent_name="product_compose_descriptions"
                )
                desc_data = json.loads(desc_response)
                descriptions = desc_data.get("descriptions", [])

                # Apply descriptions to products
                for i, desc in enumerate(descriptions):
                    if i < len(all_products_for_desc):
                        all_products_for_desc[i]["description"] = desc
                logger.info(f"[product_compose] Generated {len(descriptions)} product descriptions")
            except Exception as desc_error:
                logger.warning(f"[product_compose] Failed to generate descriptions: {desc_error}")

        # Cross-retailer price comparison — tag products with best price badges
        price_comparisons = _find_price_comparisons(products_by_provider) if len(products_by_provider) >= 2 else {}
        if price_comparisons:
            logger.info(f"[product_compose] Found {len(price_comparisons)} cross-retailer price comparisons")
            for provider_name, data in products_by_provider.items():
                for product in data["products"]:
                    title = product.get("title", "")
                    for comp_key, comp_data in price_comparisons.items():
                        if _fuzzy_product_match(title, comp_key, threshold=0.5):
                            if comp_data["best_retailer"] == provider_name:
                                product["best_price"] = True
                                product["savings"] = comp_data["savings"]
                                if comp_data["other_prices"]:
                                    product["compared_retailer"] = comp_data["other_prices"][0]["retailer"].title()
                            break

        # Add products to UI blocks
        for provider_name, data in products_by_provider.items():
            ui_blocks.append({
                "type": data["config"]["type"],
                "title": data["config"]["title"],
                "data": data["products"]
            })
            logger.info(f"[product_compose] Added {len(data['products'])} {provider_name} products to UI")

        # Create citations
        citations = [p["url"] for p in normalized_products if p.get("url")][:5]

        # Log summary
        provider_summary = ", ".join([f"{len(affiliate_products.get(p, []))} {p}" for p in sorted_providers])
        logger.info(f"[product_compose] Generated response: {len(assistant_text)} chars, providers: {provider_summary}")

        # Build search context for follow-up queries
        product_names = [p.get("name", "") for p in normalized_products if p.get("name")]
        new_context = {
            "category": slots.get("category", "") if slots else "",
            "product_type": slots.get("product_type", "") if slots else "",
            "product_names": product_names,
            "budget": slots.get("budget") if slots else None,
            "brand": slots.get("brand") if slots else None,
            "features": slots.get("features") if slots else None,
            "use_case": slots.get("use_case") if slots else None,
            "top_prices": {
                p["name"]: p["best_offer"]["price"]
                for p in products_with_offers
                if p.get("best_offer", {}).get("price")
            },
            "avg_rating": {
                name: rd.get("avg_rating", 0)
                for name, rd in review_data.items()
            } if review_data else {},
            "query": user_message,
            "timestamp": datetime.utcnow().isoformat(),
            "turn_index": len(state.get("conversation_history", [])),
        }

        # Push previous context to history
        prev = state.get("last_search_context", {})
        history = list(state.get("search_history", []))
        if prev:
            history.append(prev)
            history = history[-5:]

        logger.info(f"[product_compose] Saving search context: category={new_context['category']}, {len(product_names)} products")

        return {
            "assistant_text": assistant_text,
            "ui_blocks": ui_blocks,
            "citations": citations,
            "last_search_context": new_context,
            "search_history": history,
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
