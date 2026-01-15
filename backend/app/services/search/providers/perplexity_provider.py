"""
Perplexity Search Provider
"""
from app.core.centralized_logger import get_logger
from typing import List, Optional
import httpx
from ..base import SearchProvider, SearchResult, SearchProviderError
from ..registry import SearchProviderRegistry

logger = get_logger(__name__)


@SearchProviderRegistry.register("perplexity")
class PerplexityProvider(SearchProvider):
    """Perplexity AI search provider"""

    def __init__(self, api_key: str, **config):
        super().__init__(api_key, **config)
        # Now configurable!
        self.base_url = config.get("base_url", "https://api.perplexity.ai")
        self.model = config.get("model", "sonar")
        self.timeout = config.get("timeout", 30.0)

        # Domain filters from config
        self.product_domains = self._parse_domains(config.get("product_domains", "ebay.com"))
        self.service_domains = self._parse_domains(config.get("service_domains", "g2.com,capterra.com,trustpilot.com"))
        self.travel_domains = self._parse_domains(config.get("travel_domains", "tripadvisor.com,lonelyplanet.com"))

    def _parse_domains(self, domains: str) -> List[str]:
        """Parse comma-separated domain string into list"""
        if isinstance(domains, str):
            return [d.strip() for d in domains.split(",") if d.strip()]
        return domains if isinstance(domains, list) else []

    def get_provider_name(self) -> str:
        return "perplexity"

    async def search(
        self,
        query: str,
        intent: Optional[str] = None,
        max_results: int = 10,
        **filters
    ) -> List[SearchResult]:
        """Search using Perplexity API"""

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                # Build payload with intent-specific optimizations
                payload = self._build_payload(query, intent, max_results)

                logger.info(f"\033[92mPerplexity search request: {query}\033[0m")
                logger.info(f"Intent: {intent}, Search mode: {payload.get('search_mode', 'default')}")

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                logger.info(f"Perplexity API status: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"Perplexity API error response: {response.text}")
                    raise SearchProviderError(f"Perplexity API returned {response.status_code}")

                response.raise_for_status()
                data = response.json()

                logger.debug(f"Perplexity raw response: {data}")

                return self._parse_response(data)

        except httpx.HTTPError as e:
            logger.error(f"Perplexity API error: {e}")
            raise SearchProviderError(f"Perplexity search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise SearchProviderError(f"Search failed: {e}")

    def _build_payload(self, query: str, intent: Optional[str], max_results: int) -> dict:
        """Build Perplexity API payload with intent-specific optimizations"""

        # Base payload structure
        payload = {
            "model": self.model,
            "return_citations": True,
            "return_related_questions": False
        }

        # Intent-specific optimizations
        if intent == "product":
            # PRODUCT INTENT: Force product-only results, no articles/blogs
            # NOTE: Perplexity API does not support "shopping" mode - use "web" with domain filters
            payload["search_mode"] = "web"

            # Enhanced query with negative keywords to exclude articles
            enhanced_query = f"{query}. Find ONLY purchasable products with real prices and URLs. Exclude articles, blogs, news, reviews, comparisons, guides, wikis."

            payload["messages"] = [
                {
                    "role": "system",
                    "content": "You are a product search specialist. Return ONLY real purchasable products. Do NOT return articles, guides, blogs, reviews, comparisons, or news. Output only product listings with price, link, and availability."
                },
                {
                    "role": "user",
                    "content": enhanced_query
                }
            ]

            # Strict domain filter for ecommerce-only sources
            # NOTE: Perplexity expects a list, not an object
            payload["search_domain_filter"] = self.product_domains

            # Structured output to force product schema
            payload["structured_output"] = {
                "schema": {
                    "type": "object",
                    "properties": {
                        "products": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "price": {"type": "string"},
                                    "url": {"type": "string"},
                                    "source": {"type": "string"},
                                    "availability": {"type": "string"}
                                },
                                "required": ["title", "url"]
                            }
                        }
                    },
                    "required": ["products"]
                }
            }

        elif intent == "service":
            # SERVICE INTENT: Reviews and comparisons
            payload["messages"] = [
                {
                    "role": "system",
                    "content": "You are a service search assistant. Provide service reviews, comparisons, and ratings with citations."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            payload["search_domain_filter"] = self.service_domains

        elif intent == "travel":
            # TRAVEL INTENT: Travel guides and recommendations
            payload["messages"] = [
                {
                    "role": "system",
                    "content": "You are a travel search assistant. Provide travel guides, destination information, and recommendations."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            payload["search_domain_filter"] = self.travel_domains

        else:
            # DEFAULT: General search
            payload["messages"] = [
                {
                    "role": "system",
                    "content": "You are a helpful search assistant. Provide relevant information with citations."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]

        return payload

    def _parse_response(self, data: dict) -> List[SearchResult]:
        """Parse Perplexity response with support for structured output"""
        results = []

        try:
            # Extract the main content from Perplexity's response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Check if this is a structured output response (for product intent)
            if isinstance(content, dict) and "products" in content:
                logger.info(f"Parsing structured product output with {len(content['products'])} products")

                # Parse structured product data
                for idx, product in enumerate(content["products"], start=1):
                    results.append(SearchResult(
                        url=product.get("url", ""),
                        title=product.get("title", f"Product {idx}"),
                        snippet=f"Price: {product.get('price', 'N/A')}\nSource: {product.get('source', 'N/A')}\nAvailability: {product.get('availability', 'N/A')}",
                        source_rank=idx,
                        freshness="recent",
                        authority_score=8  # High authority for direct product listings
                    ))

                return results

            # Handle string content (JSON string for structured output or regular text)
            if isinstance(content, str):
                # Try to parse as JSON (structured output might be returned as string)
                try:
                    import json
                    parsed_content = json.loads(content)
                    if isinstance(parsed_content, dict) and "products" in parsed_content:
                        logger.info(f"Parsing JSON structured product output with {len(parsed_content['products'])} products")

                        for idx, product in enumerate(parsed_content["products"], start=1):
                            results.append(SearchResult(
                                url=product.get("url", ""),
                                title=product.get("title", f"Product {idx}"),
                                snippet=f"Price: {product.get('price', 'N/A')}\nSource: {product.get('source', 'N/A')}\nAvailability: {product.get('availability', 'N/A')}",
                                source_rank=idx,
                                freshness="recent",
                                authority_score=8
                            ))

                        return results
                except (json.JSONDecodeError, ValueError):
                    # Not JSON, continue with regular text parsing
                    pass

            # Regular text content parsing (non-structured output)
            # Get search_results and citations for URLs
            search_results = data.get("search_results", [])
            citations = data.get("citations", [])

            if content:
                # Primary result: Use the full content as the main search result
                logger.info(f"Using Perplexity content with {len(content)} characters")

                results.append(SearchResult(
                    url="",  # Content-based result has no direct URL
                    title="Perplexity AI Response",
                    snippet=content,  # Store the FULL content, not just a snippet
                    source_rank=1,
                    freshness="recent",
                    authority_score=10  # Highest authority - this is the synthesized answer
                ))

                # Add source URLs from search_results for citation purposes
                if search_results:
                    logger.info(f"Adding {len(search_results)} source URLs from search_results")
                    for idx, result in enumerate(search_results, start=2):
                        results.append(SearchResult(
                            url=result.get("url", ""),
                            title=result.get("title", f"Source {idx - 1}"),
                            snippet=result.get("snippet", ""),
                            source_rank=idx,
                            freshness=result.get("date", "recent"),
                            authority_score=5
                        ))
                elif citations:
                    # Fallback: Use citations if no search_results
                    logger.info(f"Adding {len(citations)} source URLs from citations")
                    for idx, citation in enumerate(citations, start=2):
                        results.append(SearchResult(
                            url=citation,
                            title=f"Source {idx - 1}",
                            snippet="",
                            source_rank=idx,
                            freshness="recent",
                            authority_score=5
                        ))
            elif search_results:
                # Fallback: Use search_results if no content (shouldn't happen normally)
                logger.warning("No content in response, falling back to search_results")
                for idx, result in enumerate(search_results):
                    results.append(SearchResult(
                        url=result.get("url", ""),
                        title=result.get("title", f"Source {idx + 1}"),
                        snippet=result.get("snippet", ""),
                        source_rank=idx + 1,
                        freshness=result.get("date", "recent"),
                        authority_score=5
                    ))
            else:
                logger.error("No content, search_results, or citations in Perplexity response")

        except Exception as e:
            logger.error(f"Error parsing Perplexity response: {e}", exc_info=True)

        return results
