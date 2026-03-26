"""
Product Affiliate Tool

Finds affiliate/monetized links for products.
Supports multiple affiliate networks dynamically based on configuration.
Returns a dictionary of provider -> products for flexible frontend rendering.
"""

import sys
import os
import asyncio
from typing import Dict, Any, List
from app.core.error_manager import tool_error_handler

# Add backend to path (portable path)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Lazy imports for Skimlinks -- graceful if Phase 6 not deployed
try:
    from app.services.affiliate.skimlinks import skimlinks_wrapper
except ImportError:
    skimlinks_wrapper = None  # type: ignore[assignment]

try:
    from app.core.config import settings
except ImportError:
    settings = None  # type: ignore[assignment]


async def _apply_skimlinks_wrapping(affiliate_products: dict, session_id: str = "") -> dict:
    """
    Post-process all provider results: wrap qualifying URLs with Skimlinks.

    Non-fatal: if anything fails, original URLs are preserved.
    Provider-agnostic: works on ALL providers without modifying them.
    """
    try:
        from app.core.centralized_logger import get_logger

        logger = get_logger(__name__)

        # Guard: skip if Skimlinks is not configured or not enabled
        if not skimlinks_wrapper:
            return affiliate_products
        if not getattr(settings, 'SKIMLINKS_API_ENABLED', False):
            return affiliate_products

        wrapped_count = 0
        for provider_name, provider_groups in affiliate_products.items():
            for group in provider_groups:
                for offer in group.get("offers", []):
                    url = offer.get("url", "")
                    if url and skimlinks_wrapper.is_supported_domain(url):
                        offer["url"] = skimlinks_wrapper.wrap_url(url, xcust=session_id)
                        offer["skimlinks_wrapped"] = True
                        wrapped_count += 1

        if wrapped_count > 0:
            logger.info(f"[product_affiliate] Skimlinks wrapped {wrapped_count} URLs")

    except ImportError:
        # Phase 6 not yet deployed -- silently skip
        pass
    except Exception as e:
        from app.core.centralized_logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"[product_affiliate] Skimlinks wrapping failed (non-fatal): {e}")

    return affiliate_products


# Tool contract for planner
TOOL_CONTRACT = {
    "name": "product_affiliate",
    "intent": "product",
    "purpose": "Find affiliate/monetization links for products from configured providers (eBay, Amazon, etc). Fetches real purchase links and prices.",
    "tools": {
        "pre": [],  # Needs normalized_products
        "post": ["product_ranking"]  # Compose is auto-added at end of intent
    },
    "produces": ["affiliate_products"],
    "citation_message": "Comparing prices across retailers...",
    "is_default": True
}


@tool_error_handler(tool_name="product_affiliate", error_message="Failed to get affiliate links")
async def product_affiliate(
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Find affiliate links for products from all configured providers.

    Reads from state:
        - normalized_products: List of normalized products (with name field)
        - slots.country_code: Optional country code for regional links

    Writes to state:
        - affiliate_products: Dict mapping provider_name -> list of product results
          Example: {"ebay": [...], "amazon": [...]}

    Returns:
        {
            "affiliate_products": {
                "ebay": [{"product_name": "...", "offers": [...]}],
                "amazon": [{"product_name": "...", "offers": [...]}],
                ...
            },
            "success": bool
        }
    """
    # Import here to avoid settings validation at module load
    from app.core.centralized_logger import get_logger
    from app.services.affiliate.manager import affiliate_manager
    from app.core.config import settings

    logger = get_logger(__name__)

    try:
        # Read from state - support both normalized_products and product_names as fallback
        products = state.get("normalized_products", [])
        product_names = state.get("product_names", [])
        max_offers = settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT

        # Get country code and category from slots, with context fallback
        slots = state.get("slots", {})
        last_search_context = state.get("last_search_context", {})
        country_code = slots.get("country_code", settings.AMAZON_DEFAULT_COUNTRY)
        category = slots.get("category") or last_search_context.get("category")

        # Prepare product names to search
        products_to_search = []

        # First try to get names from normalized_products
        if products:
            for product in products[:8]:  # Limit to top 8 products
                product_name = product.get("title") or product.get("name") or ""
                if product_name:
                    products_to_search.append(product_name)

        # Fallback to product_names if normalized_products is empty
        if not products_to_search and product_names:
            logger.info("[product_affiliate] Using product_names as fallback (normalized_products was empty)")
            products_to_search = product_names[:8]

        logger.info(f"[product_affiliate] Finding links for {len(products_to_search)} products (country={country_code})")

        if not products_to_search:
            return {
                "affiliate_products": {},
                "success": True
            }

        # Check for curated Amazon links matching the user's query
        user_message = state.get("user_message", "")
        curated_amazon_links = None
        try:
            from app.services.affiliate.providers.curated_amazon_links import find_curated_links
            curated_amazon_links = find_curated_links(user_message)
            if not curated_amazon_links and category:
                curated_amazon_links = find_curated_links(category)
            if curated_amazon_links:
                logger.info(f"[product_affiliate] Found {len(curated_amazon_links)} curated Amazon links for query")
        except Exception as e:
            logger.warning(f"[product_affiliate] Curated link lookup failed: {e}")

        # When USE_CURATED_LINKS is on, curated links are the ONLY source.
        # Skip all live API provider searches.
        if curated_amazon_links and settings.USE_CURATED_LINKS:
            results = []
            for i, product_name in enumerate(products_to_search):
                if i < min(len(curated_amazon_links), 5):
                    curated = curated_amazon_links[i]
                    if isinstance(curated, dict):
                        link = curated.get("url", "")
                        title = curated.get("title", product_name)
                        price = curated.get("price", 0)
                        image = curated.get("image_url", "")
                    else:
                        link = curated
                        title = product_name
                        price = 0
                        image = ""
                    results.append({
                        "product_name": product_name,
                        "offers": [{
                            "product_id": f"curated-{curated.get('asin', i)}" if isinstance(curated, dict) else f"curated-{i}",
                            "title": title,
                            "price": price,
                            "currency": "USD",
                            "url": link,
                            "image_url": image,
                            "merchant": "Amazon",
                            "rating": None,
                            "review_count": None,
                            "source": "amazon",
                        }]
                    })
            # Cap at 5 products
            results = results[:5]
            # Apply Skimlinks wrapping even to curated results
            curated_affiliate = {"amazon": results} if results else {}
            session_id = state.get("session_id", "")
            curated_affiliate = await _apply_skimlinks_wrapping(curated_affiliate, session_id)
            logger.info(f"[product_affiliate] USE_CURATED_LINKS=true: returning {len(results)} curated Amazon links (skipping live APIs)")
            return {
                "affiliate_products": curated_affiliate,
                "success": True
            }

        # Get all available providers from the manager
        available_providers = affiliate_manager.get_available_providers()
        # Filter out "mock" provider - we want real affiliate providers
        providers_to_use = [p for p in available_providers if p != "mock"]

        logger.info(f"[product_affiliate] Using providers: {providers_to_use}")

        # Helper function to search a single product on a single provider
        async def search_single_product(provider, provider_name: str, product_name: str) -> Dict[str, Any]:
            """Search one product on one provider."""
            try:
                search_kwargs = {
                    "query": product_name,
                    "limit": max_offers,
                    "category": category,
                }

                # Add country_code for providers that support it
                if hasattr(provider, 'search_products'):
                    import inspect
                    sig = inspect.signature(provider.search_products)
                    if 'country_code' in sig.parameters:
                        search_kwargs['country_code'] = country_code

                search_results = await provider.search_products(**search_kwargs)

                if search_results:
                    offers = []
                    for result in search_results:
                        offer = {
                            "merchant": getattr(result, 'merchant', provider_name.title()),
                            "price": getattr(result, 'price', 0),
                            "currency": getattr(result, 'currency', "USD"),
                            "url": getattr(result, 'affiliate_link', ""),
                            "condition": getattr(result, 'condition', "new"),
                            "title": getattr(result, 'title', ""),
                            "image_url": getattr(result, 'image_url', ""),
                            "rating": getattr(result, 'rating', None),
                            "review_count": getattr(result, 'review_count', None),
                            "source": provider_name
                        }
                        if hasattr(result, 'product_id') and result.product_id:
                            offer["product_id"] = result.product_id
                        offers.append(offer)

                    return {"product_name": product_name, "offers": offers}

            except Exception as e:
                logger.warning(f"[product_affiliate] {provider_name} search failed for {product_name}: {e}")

            return None

        # Helper function to search a provider for all products (in parallel)
        async def search_provider(provider_name: str) -> Dict[str, Any]:
            """Search all products on a single provider using asyncio.gather."""
            # For Amazon: use curated links if available (matched against user query)
            if provider_name == "amazon" and curated_amazon_links:
                results = []
                for i, product_name in enumerate(products_to_search):
                    if i < min(len(curated_amazon_links), 5):
                        curated = curated_amazon_links[i]
                        # Support both old format (string URL) and new format (dict with metadata)
                        if isinstance(curated, dict):
                            link = curated.get("url", "")
                            title = curated.get("title", product_name)
                            price = curated.get("price", 0)
                            image = curated.get("image_url", "")
                        else:
                            link = curated
                            title = product_name
                            price = 0
                            image = ""
                        results.append({
                            "product_name": product_name,
                            "offers": [{
                                "merchant": "Amazon",
                                "price": price,
                                "currency": "USD",
                                "url": link,
                                "condition": "new",
                                "title": title,
                                "image_url": image,
                                "rating": None,
                                "review_count": None,
                                "source": "amazon",
                            }]
                        })
                logger.info(f"[product_affiliate] Amazon: used {len(results)} curated links (matched user query)")
                return {"provider": provider_name, "results": results}

            provider = affiliate_manager.get_provider(provider_name)
            if not provider:
                return {"provider": provider_name, "results": []}

            tasks = [
                search_single_product(provider, provider_name, name)
                for name in products_to_search
            ]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            results = []
            for r in raw_results:
                if isinstance(r, Exception):
                    logger.warning(f"[product_affiliate] {provider_name} product search exception: {r}")
                elif r is not None:
                    results.append(r)

            return {"provider": provider_name, "results": results}

        # Execute searches for all providers in parallel
        logger.info(f"[product_affiliate] Starting parallel search for {len(products_to_search)} products on {len(providers_to_use)} providers")

        tasks = [search_provider(provider_name) for provider_name in providers_to_use]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build the affiliate_products dictionary
        affiliate_products = {}
        for result in all_results:
            if isinstance(result, Exception):
                logger.warning(f"[product_affiliate] Provider search failed: {result}")
                continue
            if result and result.get("results"):
                provider_name = result["provider"]
                affiliate_products[provider_name] = result["results"]
                logger.info(f"[product_affiliate] Found {len(result['results'])} product groups from {provider_name}")

        logger.info(f"[product_affiliate] Total providers with results: {list(affiliate_products.keys())}")

        # Apply Skimlinks wrapping to qualifying URLs (Phase 7 middleware)
        session_id = state.get("session_id", "")
        affiliate_products = await _apply_skimlinks_wrapping(affiliate_products, session_id)

        return {
            "affiliate_products": affiliate_products,
            "success": True
        }

    except Exception as e:
        logger.error(f"[product_affiliate] Error: {e}", exc_info=True)
        return {
            "affiliate_products": {},
            "error": str(e),
            "success": False
        }
