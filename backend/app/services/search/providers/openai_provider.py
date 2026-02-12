"""
OpenAI Search Provider
Uses OpenAI's GPT models for web search and product name extraction
"""
from app.core.centralized_logger import get_logger
from typing import List, Optional, Dict, Any
import httpx
from ..base import SearchProvider, SearchResult, SearchProviderError
from ..registry import SearchProviderRegistry
from app.core.config import settings

logger = get_logger(__name__)


@SearchProviderRegistry.register("openai")
class OpenAIProvider(SearchProvider):
    """OpenAI search provider using GPT models"""

    def __init__(self, api_key: str, **config):
        super().__init__(api_key, **config)
        # Now configurable from .env!
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4o-mini")
        self.timeout = config.get("timeout", 30.0)

        # Domain filters from config
        self.product_domains = self._parse_domains(config.get("product_domains", ""))
        self.service_domains = self._parse_domains(config.get("service_domains", ""))
        self.travel_domains = self._parse_domains(config.get("travel_domains", ""))

    def _parse_domains(self, domains: str) -> List[str]:
        """Parse comma-separated domain string into list"""
        if isinstance(domains, str):
            return [d.strip() for d in domains.split(",") if d.strip()]
        return domains if isinstance(domains, list) else []

    def get_provider_name(self) -> str:
        return "openai"

    async def search(
        self,
        query: str,
        intent: Optional[str] = None,
        max_results: int = 10,
        **filters
    ) -> List[SearchResult]:
        """Search using OpenAI API with web search capabilities

        Args:
            query: Search query
            intent: Intent type (product, travel, general, etc.)
            max_results: Maximum number of results
            **filters: Additional filters including conversation_history
        """
        # Get conversation history from filters (passed from caller, already loaded from state)
        conversation_history = filters.pop("conversation_history", None)
        if conversation_history:
            logger.info(f"Using {len(conversation_history)} messages from conversation history")

        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                # Build payload with intent-specific optimizations
                payload = self._build_payload(query, intent, max_results, conversation_history)

                logger.info(f"\033[92mOpenAI search request: {query}\033[0m")
                logger.info(f"Intent: {intent}, Model: {self.model}")

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                logger.info(f"OpenAI API status: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"OpenAI API error response: {response.text}")
                    raise SearchProviderError(f"OpenAI API returned {response.status_code}")

                response.raise_for_status()
                data = response.json()

                logger.debug(f"OpenAI raw response: {data}")

                return self._parse_response(data, intent)

        except httpx.HTTPError as e:
            logger.error(f"OpenAI API error: {e}")
            raise SearchProviderError(f"OpenAI search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise SearchProviderError(f"Search failed: {e}")

    def _build_payload(
        self,
        query: str,
        intent: Optional[str],
        max_results: int,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> dict:
        """Build OpenAI API payload with intent-specific optimizations

        Args:
            query: Search query
            intent: Intent type
            max_results: Maximum results
            conversation_history: Optional conversation history to include for context
        """
        # Base payload structure
        payload = {
            "model": self.model,
            "temperature": 0.3,  # Lower temperature for more focused results
        }

        # Build history messages if provided
        history_messages = []
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    # Truncate long messages to avoid token limits
                    truncated_content = content[:500] + "..." if len(content) > 500 else content
                    history_messages.append({
                        "role": role,
                        "content": truncated_content
                    })

        # Intent-specific optimizations
        if intent == "product":
            # PRODUCT INTENT: Extract product names from search query
            enhanced_query = f"""Search for products matching this query: {query}

Return a list of specific product names (brand + model) that match this query.
Focus on ACTUAL products that can be purchased, not generic categories.

Guidelines:
- Include brand and model in the product name (e.g., "iPhone 15 Pro", "Sony WH-1000XM5", "Dell XPS 15")
- Return up to {max_results} product names
- Do NOT include generic categories (e.g., "laptop", "headphones")
- Do NOT include article titles or blog posts
- Prioritize popular and relevant products from domains like: {', '.join(self.product_domains)}

Return ONLY a JSON array of product name strings, nothing else.
Example format: ["iPhone 15 Pro", "Samsung Galaxy S24 Ultra", "Google Pixel 8 Pro"]"""

            messages = [
                {
                    "role": "system",
                    "content": "You are a product search specialist. Extract and return ONLY real purchasable product names (brand + model). Return results as a JSON array of strings."
                }
            ]
            # Add history messages for context
            messages.extend(history_messages)
            messages.append({
                "role": "user",
                "content": enhanced_query
            })
            payload["messages"] = messages

            # Use response format for structured output (JSON mode)
            payload["response_format"] = {"type": "json_object"}

        elif intent == "service":
            # SERVICE INTENT: Find services and reviews
            messages = [
                {
                    "role": "system",
                    "content": f"You are a service search assistant. Find information about services, reviews, and comparisons. Prioritize results from: {', '.join(self.service_domains)}"
                }
            ]
            messages.extend(history_messages)
            messages.append({
                "role": "user",
                "content": f"Find information about: {query}\n\nProvide service names, reviews, and comparisons with sources."
            })
            payload["messages"] = messages

        elif intent == "travel":
            # TRAVEL INTENT: Travel guides and recommendations
            messages = [
                {
                    "role": "system",
                    "content": f"You are a travel search assistant. Provide travel guides, destination information, and recommendations. Prioritize sources from: {', '.join(self.travel_domains)}"
                }
            ]
            messages.extend(history_messages)
            messages.append({
                "role": "user",
                "content": f"Find travel information about: {query}"
            })
            payload["messages"] = messages

        else:
            # DEFAULT: General search
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful search assistant. Provide relevant information based on the query."
                }
            ]
            messages.extend(history_messages)
            messages.append({
                "role": "user",
                "content": query
            })
            payload["messages"] = messages

        return payload

    def _parse_response(self, data: dict, intent: Optional[str]) -> List[SearchResult]:
        """Parse OpenAI response"""
        results = []

        try:
            # Extract the main content from OpenAI's response
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not content:
                logger.error("No content in OpenAI response")
                return results

            # For product intent, parse JSON array of product names
            if intent == "product":
                import json
                try:
                    # Try to parse as JSON
                    parsed_content = json.loads(content)

                    # Handle different JSON structures
                    product_names = []
                    if isinstance(parsed_content, dict):
                        # Check for error message first
                        if "error" in parsed_content:
                            logger.warning(f"OpenAI returned error: {parsed_content['error']}")
                            return results  # Return empty results

                        # Could be {"products": [...]} or {"product_names": [...]}
                        product_names = (
                            parsed_content.get("products", []) or
                            parsed_content.get("product_names", []) or
                            parsed_content.get("results", [])
                        )

                        # Only use first value as fallback if it's a list
                        if not product_names and parsed_content:
                            first_value = list(parsed_content.values())[0]
                            if isinstance(first_value, list):
                                product_names = first_value
                            else:
                                logger.warning(f"Unexpected JSON structure: {parsed_content}")
                                return results
                    elif isinstance(parsed_content, list):
                        # Direct array of product names
                        product_names = parsed_content

                    logger.info(f"Parsed {len(product_names)} product names from OpenAI response")

                    # Create SearchResult for each product name
                    for idx, product_name in enumerate(product_names, start=1):
                        if isinstance(product_name, str) and product_name.strip():
                            title = product_name.strip()
                            # Generate unique placeholder URL based on title
                            url = f"ai://product/{idx}/{title.lower().replace(' ', '-')[:50]}"
                            results.append(SearchResult(
                                url=url,
                                title=title,
                                snippet=f"Product suggestion from OpenAI: {title}",
                                source_rank=idx,
                                freshness="recent",
                                authority_score=7  # Good authority for AI-suggested products
                            ))
                        elif isinstance(product_name, dict):
                            # Handle case where product names are objects
                            name = product_name.get("name") or product_name.get("title") or product_name.get("product")
                            if name:
                                # Use provided URL or generate unique placeholder
                                url = product_name.get("url") or f"ai://product/{idx}/{name.lower().replace(' ', '-')[:50]}"
                                results.append(SearchResult(
                                    url=url,
                                    title=name,
                                    snippet=product_name.get("description", f"Product suggestion: {name}"),
                                    source_rank=idx,
                                    freshness="recent",
                                    authority_score=7
                                ))

                except json.JSONDecodeError:
                    logger.warning("Failed to parse OpenAI response as JSON, falling back to text parsing")
                    # Fallback: try to extract product names from text
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    for idx, line in enumerate(lines, start=1):
                        # Remove numbering, bullets, quotes
                        cleaned = line.strip('- *"\'').strip()
                        if cleaned and not cleaned.startswith('[') and not cleaned.startswith('{'):
                            # Generate unique placeholder URL
                            url = f"ai://product/{idx}/{cleaned.lower().replace(' ', '-')[:50]}"
                            results.append(SearchResult(
                                url=url,
                                title=cleaned,
                                snippet=f"Product suggestion: {cleaned}",
                                source_rank=idx,
                                freshness="recent",
                                authority_score=6
                            ))

            else:
                # For non-product intents, return the full content as a single result
                logger.info(f"Using OpenAI content with {len(content)} characters")

                results.append(SearchResult(
                    url="",
                    title="OpenAI Response",
                    snippet=content,
                    source_rank=1,
                    freshness="recent",
                    authority_score=8  # High authority for AI-generated content
                ))

        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {e}", exc_info=True)

        return results
