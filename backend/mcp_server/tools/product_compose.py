"""
Product Compose Tool

Formats final product response with UI blocks and citations.
"""

import asyncio
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
    "citation_message": "Putting together your recommendations...",
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


def _fuzzy_product_match(query_name: str, candidate_name: str, threshold: float = 0.35) -> bool:
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

        # ── Phase 1: Build products_by_provider (pure data, needed by LLM prompts) ──

        sorted_providers = sorted(
            affiliate_products.keys(),
            key=lambda p: PROVIDER_CONFIG.get(p, {}).get("order", 999)
        )

        all_products_for_desc = []
        products_by_provider = {}

        for provider_name in sorted_providers:
            provider_data = affiliate_products.get(provider_name, [])
            if not provider_data:
                continue

            config = PROVIDER_CONFIG.get(provider_name, {
                "title": f"Shop on {provider_name.title()}",
                "type": f"{provider_name}_products",
                "order": 999
            })

            provider_products = []
            for affiliate_group in provider_data:
                if affiliate_group.get("offers"):
                    for offer in affiliate_group["offers"][:5]:
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
                        if offer.get("product_id"):
                            product_item["product_id"] = offer["product_id"]
                        provider_products.append(product_item)
                        all_products_for_desc.append(product_item)

            if provider_products:
                products_by_provider[provider_name] = {
                    "config": config,
                    "products": provider_products[:10]
                }

        num_products = sum(len(d["products"]) for d in products_by_provider.values())
        num_providers = len(products_by_provider)

        # ── Phase 2: Prepare all LLM coroutines (fired in parallel) ──

        llm_tasks = {}  # key -> coroutine

        # --- Assistant text: concierge OR opener (mutually exclusive with review consensus) ---
        assistant_text = ""
        if comparison_html:
            comp_product_names = comparison_data.get("products", []) if comparison_data else []
            assistant_text = f"## Product Comparison: {', '.join(comp_product_names)}\n\nHere's a detailed specification comparison."
        elif not review_data:
            # Concierge-style summary
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
            user_prefs = (state.get("metadata") or {}).get("user_preferences", {})
            pref_note = ""
            if user_prefs.get("brands") or user_prefs.get("categories"):
                past_cats = list(user_prefs.get("categories", {}).keys())[:2]
                past_brands = list(user_prefs.get("brands", {}).keys())[:2]
                parts = []
                if past_cats:
                    parts.append(f"often searches for {', '.join(past_cats)}")
                if past_brands:
                    parts.append(f"favors {', '.join(past_brands)}")
                pref_note = f"\nReturning user who {' and '.join(parts)}."

            llm_tasks['concierge'] = model_service.generate(
                messages=[
                    {"role": "system", "content": "You are ReviewGuide, a friendly and knowledgeable AI shopping assistant. Never open with phrases like 'Based on X sources' or mention how many sources you searched. Never describe your process. Write 2-3 SHORT sentences (max 60 words). Explain WHY these products match the user's needs. Reference their criteria from the conversation (budget, features, use case). Do NOT list products — they are shown in cards below. End with a brief, warm follow-up that shows you remember the user's context."},
                    {"role": "user", "content": f'User asked: "{user_message}"\nContext:\n{context_summary}{pref_note}\nProducts: {", ".join(product_name_list)}\nSources: {", ".join(provider_names)}'}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=120,
                agent_name="product_compose"
            )

        # --- Review consensus (one per product) + opener ---
        review_bundles = {}  # product_name -> bundle (for assembly later)
        if review_data:
            for product_name, bundle in review_data.items():
                if not bundle.get("sources"):
                    continue
                review_bundles[product_name] = bundle
                source_snippets = "\n".join([
                    f"- {s.get('site_name', 'Review')}: {s.get('snippet', '')}"
                    for s in bundle.get("sources", [])[:5]
                ])
                llm_tasks[f'consensus:{product_name}'] = model_service.generate(
                    messages=[
                        {"role": "system", "content": "You summarize product review consensus. Never open with 'Based on X sources' or mention how many sources you searched. Write 2-3 sentences explaining why this product is highly rated. Mention specific strengths reviewers agree on. Weave in source names only when it adds credibility (e.g., 'Wirecutter highlights its noise cancellation' rather than 'According to Wirecutter and RTINGS...'). Be concise and factual."},
                        {"role": "user", "content": f"Product: {product_name}\nAvg Rating: {bundle.get('avg_rating', 0)}/5 from {bundle.get('total_reviews', 0)} reviews\n\nReview excerpts:\n{source_snippets}\n\nWrite a 2-3 sentence consensus summary."}
                    ],
                    model=settings.COMPOSER_MODEL,
                    temperature=0.5,
                    max_tokens=120,
                    agent_name="review_consensus"
                )

            # Opener (only depends on user_message, independent of consensus)
            # Only queue if we actually have bundles with sources
            if review_bundles:
                llm_tasks['opener'] = model_service.generate(
                    messages=[
                        {"role": "system", "content": "Write a warm 1-2 sentence intro for product review results. Reference what the user asked for — their budget, use case, or features. Sound like a knowledgeable friend, not a search engine. NEVER mention source counts, number of reviews, or 'trusted sources'. Never describe your process. Respond immediately in a conversational tone. Max 30 words."},
                        {"role": "user", "content": f'User asked: "{user_message}"'}
                    ],
                    model=settings.COMPOSER_MODEL,
                    temperature=0.7,
                    max_tokens=60,
                    agent_name="product_opener"
                )

        # --- Personalized product descriptions ---
        if all_products_for_desc:
            products_to_describe = all_products_for_desc[:15]
            product_titles = [p["title"][:50] for p in products_to_describe]
            conversation_history = state.get("conversation_history", [])
            desc_context = ""
            if conversation_history:
                recent_messages = conversation_history[-6:]
                desc_context = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
                    for msg in recent_messages if msg.get('content')
                ])

            desc_system = """Generate personalized 15-20 word descriptions for each product.

IMPORTANT RULES:
1. If user mentioned a pet name (like "Max", "Bella"), reference it: "Your dog Max would love this because..."
2. If user mentioned a person (girlfriend, baby, mom), personalize: "Perfect gift for your girlfriend..."
3. If no specific context, ask a follow-up question in the description: "Great choice! What breed is your dog?"
4. Vary your descriptions - don't repeat the same pattern
5. Be warm and conversational, not generic

Return JSON: {"descriptions": ["desc1", "desc2", ...]}"""

            desc_user = f'''Conversation context:
{desc_context if desc_context else "No prior context"}

User's current question: "{user_message}"

Products to describe:
{json.dumps(product_titles)}'''

            llm_tasks['descriptions'] = model_service.generate(
                messages=[
                    {"role": "system", "content": desc_system},
                    {"role": "user", "content": desc_user}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=600,
                response_format={"type": "json_object"},
                agent_name="product_compose_descriptions"
            )

        # --- Conclusion ---
        if products_by_provider:
            llm_tasks['conclusion'] = model_service.generate(
                messages=[
                    {"role": "system", "content": f"Today is {datetime.utcnow().strftime('%B %Y')}. Write ONE short sentence (max 25 words) wrapping up a product search. Mention the number of results and where they're from. Be warm and conversational. Never describe your process or mention 'sources'. Do NOT list products or prices. Do NOT use markdown."},
                    {"role": "user", "content": f'User asked: "{user_message}"\nShowing {num_products} products from {num_providers} retailer(s). Providers: {", ".join(products_by_provider.keys())}'}
                ],
                model=settings.COMPOSER_MODEL,
                temperature=0.7,
                max_tokens=50,
                agent_name="product_conclusion"
            )

        # ── Phase 3: Fire all LLM calls in parallel ──

        task_keys = list(llm_tasks.keys())
        if task_keys:
            results = await asyncio.gather(*llm_tasks.values(), return_exceptions=True)
            result_map = dict(zip(task_keys, results))
            logger.info(f"[product_compose] Parallel LLM batch: {len(task_keys)} calls ({', '.join(task_keys)})")
        else:
            result_map = {}

        # Helper to safely extract a string result
        def _get_result(key: str, fallback: str = "") -> str:
            val = result_map.get(key)
            if val is None or isinstance(val, Exception):
                if isinstance(val, Exception):
                    logger.warning(f"[product_compose] LLM call '{key}' failed: {val}")
                return fallback
            if not isinstance(val, str):
                logger.warning(f"[product_compose] LLM call '{key}' returned non-string: {type(val)}")
                return fallback
            return val.strip()

        # ── Phase 4: Assemble results ──

        # Concierge text (non-review path)
        if 'concierge' in result_map:
            assistant_text = _get_result('concierge', fallback="Here's what I found for you.")

        # Review sources block
        ui_blocks = []
        if review_data and review_bundles:
            review_products = []
            for product_name, bundle in review_bundles.items():
                consensus = _get_result(f'consensus:{product_name}')
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
                    "data": {"products": review_products}
                })

                # Build assistant_text from opener + per-product highlights
                assistant_text = _get_result('opener')
                if assistant_text:
                    assistant_text += "\n\n"
                for rp in review_products[:3]:
                    if rp["consensus"]:
                        assistant_text += f"**{rp['name']}** — {rp['consensus']}\n\n"

                logger.info(f"[product_compose] Added review_sources block with {len(review_products)} products")

        # Comparison HTML block
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

        # Apply descriptions to products
        if 'descriptions' in result_map:
            desc_raw = _get_result('descriptions')
            if desc_raw:
                try:
                    desc_data = json.loads(desc_raw)
                    descriptions = desc_data.get("descriptions", [])
                    for i, desc in enumerate(descriptions):
                        if i < len(all_products_for_desc):
                            all_products_for_desc[i]["description"] = desc
                    logger.info(f"[product_compose] Generated {len(descriptions)} product descriptions")
                except (json.JSONDecodeError, Exception) as desc_error:
                    logger.warning(f"[product_compose] Failed to parse descriptions: {desc_error}")

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

        # Build unified price comparison block
        if price_comparisons:
            comparison_items = []
            for comp_key, comp_data in price_comparisons.items():
                offers = []
                for provider_name, data in products_by_provider.items():
                    for product in data["products"]:
                        if _fuzzy_product_match(product.get("title", ""), comp_key, threshold=0.5):
                            offers.append({
                                "merchant": provider_name.title(),
                                "price": product.get("price", 0),
                                "url": product.get("url", ""),
                                "image_url": product.get("image_url", ""),
                                "rating": product.get("rating"),
                                "review_count": product.get("review_count"),
                                "best": provider_name == comp_data["best_retailer"],
                            })
                            break
                if len(offers) >= 2:
                    comparison_items.append({
                        "product_name": comp_key,
                        "image_url": offers[0].get("image_url", ""),
                        "savings": comp_data["savings"],
                        "offers": sorted(offers, key=lambda x: x["price"]),
                    })

            if comparison_items:
                ui_blocks.insert(0, {
                    "type": "price_comparison",
                    "title": "Price Comparison",
                    "data": comparison_items,
                })
                logger.info(f"[product_compose] Added price_comparison block with {len(comparison_items)} products")

        # Add provider carousel blocks
        for provider_name, data in products_by_provider.items():
            ui_blocks.append({
                "type": data["config"]["type"],
                "title": data["config"]["title"],
                "data": data["products"]
            })
            logger.info(f"[product_compose] Added {len(data['products'])} {provider_name} products to UI")

        # Conclusion block
        conclusion_text = _get_result(
            'conclusion',
            f"Showing {num_products} results across {num_providers} retailer{'s' if num_providers != 1 else ''} — prices and availability may vary."
        )
        ui_blocks.append({
            "type": "conclusion",
            "data": {"text": conclusion_text}
        })
        logger.info(f"[product_compose] Added conclusion block: {conclusion_text[:80]}")

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
                if (p.get("best_offer") or {}).get("price")
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

        # Fire-and-forget: extract preferences from this query for cross-session memory
        meta_user_id = (state.get("metadata") or {}).get("user_id")
        if meta_user_id and slots:
            from app.services.preference_service import update_user_preferences
            asyncio.create_task(update_user_preferences(meta_user_id, slots or {}, new_context))

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
