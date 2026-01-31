# Tiered API Routing System - Design Document

**Date:** 2026-01-31
**Status:** Ready for Implementation
**Author:** Design session with Claude

---

## 1. Overview

### Problem Statement

ReviewGuide.ai needs a legally compliant, cost-efficient API routing system that:
- Avoids scraping and uses only licensed data sources
- Escalates through API tiers based on data sufficiency
- Requires explicit user consent for high-risk APIs (Tier 3-4)
- Tracks API costs for billing and observability

### Solution

A **hybrid routing system** that uses deterministic rules for common intents (product, travel, price, comparison) and falls back to the existing LLM planner for ambiguous queries (general, unclear).

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Routing approach | Hybrid (rules + LLM fallback) | Rules handle 80% of cases; LLM handles edge cases |
| Tier escalation | Count-based thresholds | Simple, predictable, no extra LLM cost |
| LLM fallback trigger | Intent-based | Only `general` and `unclear` intents use LLM planner |
| Tier 3-4 consent | Two-layer (account toggle + per-query) | Legal protection with paper trail |
| Partial failure handling | Graceful degradation + circuit breaker | No retries; tier escalation is the fallback |
| Cost tracking | PostgreSQL table | Simple, queryable for billing |

---

## 2. Architecture

### System Flow

```
User Message
     │
     ▼
[Safety Agent] ─── unchanged
     │
     ▼
[Intent Agent] ─── unchanged, outputs intent type
     │
     ▼
[Clarifier Agent] ─── slot filling for all intents
     │
     ▼
┌────────────────────────────────────────────┐
│            ROUTING GATE                    │
│                                            │
│  IF intent in [product, travel, price,     │
│     comparison, review_deep_dive]:         │
│       → Tiered API Orchestrator            │
│                                            │
│  ELSE (general, unclear, intro):           │
│       → LLM Planner (existing)             │
└────────────────────────────────────────────┘
     │
     ├─── Tiered Path ───┐
     │                   ▼
     │            [TieredAPIOrchestrator]
     │                   │
     │         ┌─────────┴─────────┐
     │         ▼                   ▼
     │    Sufficient          Consent Required
     │         │                   │
     │         ▼                   ▼
     │    Synthesizer         [HALT] → User
     │                              │
     │                         User Consents
     │                              │
     │                              ▼
     │                    Resume Orchestrator
     │                              │
     │                              ▼
     │                         Synthesizer
     │
     └─── LLM Path ───────────────────────────┐
                                              ▼
                                    [Planner → Executor]
                                              │
                                              ▼
                                         Synthesizer
```

### New Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `TieredAPIRouter` | `backend/app/services/tiered_router/router.py` | Deterministic API selection by intent + tier |
| `APIRegistry` | `backend/app/services/tiered_router/api_registry.py` | API configs, costs, feature flags |
| `ParallelFetcher` | `backend/app/services/tiered_router/parallel_fetcher.py` | Concurrent API calls with circuit breaker |
| `DataValidator` | `backend/app/services/tiered_router/data_validator.py` | Threshold checking, escalation decisions |
| `TieredAPIOrchestrator` | `backend/app/services/tiered_router/orchestrator.py` | Main coordinator |
| `routing_gate_node` | `backend/app/services/langgraph/nodes/routing_gate.py` | LangGraph node for routing decision |
| `tiered_executor_node` | `backend/app/services/langgraph/nodes/tiered_executor.py` | LangGraph node wrapping orchestrator |

---

## 3. Tiered API Router

### Routing Table

```python
TIER_ROUTING_TABLE = {
    "product": {
        1: ["amazon_affiliate", "walmart_affiliate", "bestbuy_affiliate",
            "ebay_affiliate", "google_cse_product"],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "comparison": {
        1: ["amazon_affiliate", "walmart_affiliate", "bestbuy_affiliate",
            "ebay_affiliate", "google_cse_product"],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "price_check": {
        1: ["amazon_affiliate", "walmart_affiliate", "bestbuy_affiliate",
            "ebay_affiliate"],
        2: ["google_shopping"],
        3: [],  # No Tier 3-4 for price checks
        4: [],
    },
    "review_deep_dive": {
        1: ["google_cse_product"],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "travel": {
        1: ["amadeus", "booking", "expedia", "google_cse_travel"],
        2: ["skyscanner", "tripadvisor"],
        3: [],
        4: [],
    },
}
```

### Router Function

```python
async def get_apis_for_tier(
    intent: str,
    tier: int,
    circuit_breaker: CircuitBreaker
) -> list[str]:
    apis = TIER_ROUTING_TABLE.get(intent, {}).get(tier, [])
    if not apis and intent not in TIER_ROUTING_TABLE:
        raise UnknownIntentError(f"No routing rules for intent: {intent}")
    return [api for api in apis if not circuit_breaker.is_open(api)]
```

---

## 4. API Registry

Maps logical API names to implementation details.

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class APIConfig:
    name: str
    mcp_tool: str
    provider: str
    cost_cents: int
    timeout_ms: int = 5000
    requires_consent: bool = False
    feature_flag: Optional[str] = None

API_REGISTRY = {
    # Tier 1 - Affiliates (free, revenue share)
    "amazon_affiliate": APIConfig(
        name="amazon_affiliate",
        mcp_tool="product_affiliate",
        provider="amazon",
        cost_cents=0,
    ),
    "ebay_affiliate": APIConfig(
        name="ebay_affiliate",
        mcp_tool="product_affiliate",
        provider="ebay",
        cost_cents=0,
    ),
    "walmart_affiliate": APIConfig(
        name="walmart_affiliate",
        mcp_tool="product_affiliate",
        provider="walmart",
        cost_cents=0,
    ),
    "bestbuy_affiliate": APIConfig(
        name="bestbuy_affiliate",
        mcp_tool="product_affiliate",
        provider="bestbuy",
        cost_cents=0,
    ),

    # Tier 1 - Search
    "google_cse_product": APIConfig(
        name="google_cse_product",
        mcp_tool="product_search",
        provider="google_cse",
        cost_cents=1,  # $5/1K queries
    ),
    "google_cse_travel": APIConfig(
        name="google_cse_travel",
        mcp_tool="travel_search",
        provider="google_cse",
        cost_cents=1,
    ),

    # Tier 2
    "bing_search": APIConfig(
        name="bing_search",
        mcp_tool="product_search",
        provider="bing",
        cost_cents=1,  # $3/1K queries
    ),
    "youtube_transcripts": APIConfig(
        name="youtube_transcripts",
        mcp_tool="product_evidence",
        provider="youtube",
        cost_cents=0,  # Free tier
    ),
    "google_shopping": APIConfig(
        name="google_shopping",
        mcp_tool="product_search",
        provider="google_shopping",
        cost_cents=1,
    ),

    # Tier 3 - Consent required
    "reddit_api": APIConfig(
        name="reddit_api",
        mcp_tool="product_evidence",
        provider="reddit",
        cost_cents=1,  # $0.24/1K calls
        requires_consent=True,
        feature_flag="ENABLE_REDDIT_API",
    ),

    # Tier 4 - High risk
    "serpapi": APIConfig(
        name="serpapi",
        mcp_tool="product_search",
        provider="serpapi",
        cost_cents=1,  # $50/5K = 1 cent per call
        requires_consent=True,
        feature_flag="ENABLE_SERPAPI",
    ),

    # Travel APIs
    "amadeus": APIConfig(
        name="amadeus",
        mcp_tool="travel_search_flights",
        provider="amadeus",
        cost_cents=0,
    ),
    "booking": APIConfig(
        name="booking",
        mcp_tool="travel_search_hotels",
        provider="booking",
        cost_cents=0,
    ),
    "expedia": APIConfig(
        name="expedia",
        mcp_tool="travel_search_hotels",
        provider="expedia",
        cost_cents=0,
    ),
    "skyscanner": APIConfig(
        name="skyscanner",
        mcp_tool="travel_search_flights",
        provider="skyscanner",
        cost_cents=0,
    ),
    "tripadvisor": APIConfig(
        name="tripadvisor",
        mcp_tool="travel_destination_facts",
        provider="tripadvisor",
        cost_cents=0,
    ),
}
```

---

## 5. Parallel Fetcher with Circuit Breaker

### Circuit Breaker

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Skip APIs that have failed repeatedly.

    States: CLOSED (normal) → OPEN (skip) → CLOSED (after timeout)

    TODO: If scaling beyond 3 workers, consider Redis-backed state
    to share failure state across workers.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout  # seconds
        self._state: dict[str, dict] = {}

    def is_open(self, api_name: str) -> bool:
        state = self._state.get(api_name)
        if not state:
            return False
        if state["open_until"] and datetime.utcnow() < state["open_until"]:
            return True
        if state["open_until"] and datetime.utcnow() >= state["open_until"]:
            self._state[api_name] = {"failures": 0, "open_until": None}
        return False

    def record_failure(self, api_name: str):
        state = self._state.setdefault(api_name, {"failures": 0, "open_until": None})
        state["failures"] += 1
        if state["failures"] >= self.failure_threshold:
            state["open_until"] = datetime.utcnow() + timedelta(seconds=self.reset_timeout)

    def record_success(self, api_name: str):
        self._state[api_name] = {"failures": 0, "open_until": None}


# Module-level singleton
_circuit_breaker = CircuitBreaker()
```

### Parallel Fetcher

```python
import asyncio
from typing import Dict, List

class ParallelFetcher:
    def __init__(self, circuit_breaker: CircuitBreaker = None):
        self.circuit_breaker = circuit_breaker or _circuit_breaker

    async def fetch_tier(
        self,
        apis: List[str],
        query: str,
        state: GraphState
    ) -> Dict[str, dict]:
        """Fetch from all APIs in a tier concurrently."""

        active_apis = [api for api in apis if not self.circuit_breaker.is_open(api)]
        skipped_apis = [api for api in apis if self.circuit_breaker.is_open(api)]

        # Actually parallel using gather
        tasks = [self._fetch_single(api, query, state) for api in active_apis]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for api, response in zip(active_apis, responses):
            if isinstance(response, Exception):
                results[api] = {"status": "error", "api": api, "error": str(response)}
            else:
                results[api] = response

        for api in skipped_apis:
            results[api] = {"status": "circuit_open", "api": api}

        return results

    async def _fetch_single(self, api_name: str, query: str, state: GraphState) -> dict:
        config = API_REGISTRY[api_name]

        try:
            result = await asyncio.wait_for(
                execute_mcp_tool(
                    tool_name=config.mcp_tool,
                    provider=config.provider,
                    query=query,
                ),
                timeout=config.timeout_ms / 1000,
            )

            self.circuit_breaker.record_success(api_name)
            await log_api_usage(
                user_id=state["user_id"],
                api_name=api_name,
                cost_cents=config.cost_cents,
                success=True,
            )
            return {"status": "success", "api": api_name, "data": result}

        except asyncio.TimeoutError:
            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state["user_id"],
                api_name=api_name,
                cost_cents=0,
                success=False,
                error="timeout",
            )
            return {"status": "timeout", "api": api_name}

        except Exception as e:
            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state["user_id"],
                api_name=api_name,
                cost_cents=0,
                success=False,
                error=str(e),
            )
            return {"status": "error", "api": api_name, "error": str(e)}
```

---

## 6. Data Validator

### Threshold Configuration

```python
from dataclasses import dataclass
from enum import Enum

class ValidationResult(Enum):
    SUFFICIENT = "sufficient"
    ESCALATE = "escalate"
    CONSENT_REQUIRED = "consent_required"
    MAX_TIER_REACHED = "max_tier_reached"

@dataclass
class ThresholdConfig:
    min_items: int = 0          # products, hotels, flights
    min_snippets: int = 0
    min_sources: int = 0        # For source diversity
    require_all_items: bool = False  # For comparison intent

INTENT_THRESHOLDS = {
    "product": ThresholdConfig(min_items=3),
    "comparison": ThresholdConfig(require_all_items=True),
    "price_check": ThresholdConfig(min_items=1),
    "review_deep_dive": ThresholdConfig(min_snippets=5, min_sources=2),
    "travel": ThresholdConfig(min_items=1, min_snippets=3),
}
```

### Validator

```python
class DataValidator:
    def __init__(self, max_auto_tier: int = 2):
        self.max_auto_tier = max_auto_tier  # Tier 3+ requires consent

    def validate(
        self,
        intent: str,
        current_tier: int,
        results: dict[str, dict],
        requested_products: list[str] = None,
        user_consent: dict = None,
    ) -> tuple[ValidationResult, dict]:
        """
        Returns (result, metadata) where metadata contains:
        - SUFFICIENT: {"sources_used": [...], "sources_unavailable": [...]}
        - ESCALATE: {"next_tier": int}
        - CONSENT_REQUIRED: {"consent_type": "account_toggle" | "per_query", "message": str}
        - MAX_TIER_REACHED: {"partial_results": True, "message": str}
        """

        threshold = INTENT_THRESHOLDS.get(intent, ThresholdConfig())

        successful = {k: v for k, v in results.items() if v.get("status") == "success"}
        failed = {k: v for k, v in results.items() if v.get("status") != "success"}

        items = self._extract_items(successful)
        snippets = self._extract_snippets(successful)
        sources_used = list(successful.keys())

        is_sufficient = self._check_threshold(
            threshold, items, snippets, requested_products, sources_used
        )

        if is_sufficient:
            return ValidationResult.SUFFICIENT, {
                "sources_used": sources_used,
                "sources_unavailable": list(failed.keys()),
                "item_count": len(items),
                "snippet_count": len(snippets),
            }

        next_tier = current_tier + 1

        if next_tier <= self.max_auto_tier:
            return ValidationResult.ESCALATE, {"next_tier": next_tier}

        if next_tier <= 4:
            user_consent = user_consent or {}

            if not user_consent.get("account_toggle"):
                return ValidationResult.CONSENT_REQUIRED, {
                    "consent_type": "account_toggle",
                    "message": "Enable Extended Search in Settings to search more sources",
                }

            if not user_consent.get("per_query"):
                return ValidationResult.CONSENT_REQUIRED, {
                    "consent_type": "per_query",
                    "message": "Search deeper?",
                    "next_tier": next_tier,
                }

            return ValidationResult.ESCALATE, {"next_tier": next_tier}

        return ValidationResult.MAX_TIER_REACHED, {
            "partial_results": True,
            "sources_used": sources_used,
            "message": "Showing results from available sources",
        }

    def _check_threshold(
        self,
        threshold: ThresholdConfig,
        items: list,
        snippets: list,
        requested_products: list = None,
        sources_used: list = None,
    ) -> bool:
        if threshold.require_all_items:
            if not requested_products:
                return len(items) >= 2
            found_names = {item.get("name", "").lower() for item in items}
            return all(
                any(req.lower() in name for name in found_names)
                for req in requested_products
            )

        if threshold.min_items and len(items) < threshold.min_items:
            return False
        if threshold.min_snippets and len(snippets) < threshold.min_snippets:
            return False
        if threshold.min_sources and len(sources_used or []) < threshold.min_sources:
            return False

        return True

    def _extract_items(self, results: dict) -> list:
        items = []
        for api_result in results.values():
            data = api_result.get("data", {})
            items.extend(data.get("products", []))
            items.extend(data.get("hotels", []))
            items.extend(data.get("flights", []))
        return items

    def _extract_snippets(self, results: dict) -> list:
        snippets = []
        for api_result in results.values():
            data = api_result.get("data", {})
            snippets.extend(data.get("snippets", []))
        return snippets
```

---

## 7. Orchestrator

```python
class TieredAPIOrchestrator:
    def __init__(self, circuit_breaker: CircuitBreaker = None):
        self.circuit_breaker = circuit_breaker or _circuit_breaker
        self.fetcher = ParallelFetcher(self.circuit_breaker)
        self.validator = DataValidator(max_auto_tier=2)

    async def execute(
        self,
        intent: str,
        query: str,
        state: GraphState,
    ) -> dict:
        """
        Returns:
        {
            "status": "success" | "consent_required" | "partial",
            "items": [...],
            "snippets": [...],
            "sources_used": [...],
            "sources_unavailable": [...],
            "consent_prompt": {...},  # If consent_required
            "tier_reached": int,
        }
        """

        current_tier = 1
        all_results = {}
        requested_items = state.get("requested_products", [])
        user_consent = {
            "account_toggle": state.get("user_extended_search_enabled", False),
            "per_query": state.get("extended_search_confirmed", False),
        }

        while current_tier <= 4:
            apis = get_apis_for_tier(intent, current_tier, self.circuit_breaker)

            if not apis:
                current_tier += 1
                continue

            apis = self._filter_by_feature_flags(apis)

            if not apis:
                current_tier += 1
                continue

            tier_results = await self.fetcher.fetch_tier(apis, query, state)
            all_results.update(tier_results)

            validation_result, metadata = self.validator.validate(
                intent=intent,
                current_tier=current_tier,
                results=all_results,
                requested_products=requested_items,
                user_consent=user_consent,
            )

            if validation_result == ValidationResult.SUFFICIENT:
                return self._build_success_response(all_results, metadata, current_tier)

            if validation_result == ValidationResult.ESCALATE:
                next_tier = metadata["next_tier"]

                # Log consent if escalating to Tier 3-4
                if next_tier >= 3:
                    await log_consent_event(
                        user_id=state["user_id"],
                        consent_type="per_query",
                        tier_requested=next_tier,
                    )

                current_tier = next_tier
                continue

            if validation_result == ValidationResult.CONSENT_REQUIRED:
                return self._build_consent_response(all_results, metadata, current_tier)

            if validation_result == ValidationResult.MAX_TIER_REACHED:
                return self._build_partial_response(all_results, metadata, current_tier)

        return self._build_partial_response(all_results, {}, current_tier)

    def _filter_by_feature_flags(self, apis: list[str]) -> list[str]:
        filtered = []
        for api in apis:
            config = API_REGISTRY.get(api)
            if config and config.feature_flag:
                if not settings.get(config.feature_flag, False):
                    continue
            filtered.append(api)
        return filtered

    def _build_success_response(self, results: dict, metadata: dict, tier: int) -> dict:
        items, snippets = self._extract_all_data(results)
        return {
            "status": "success",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get("sources_used", []),
            "sources_unavailable": metadata.get("sources_unavailable", []),
            "tier_reached": tier,
        }

    def _build_consent_response(self, results: dict, metadata: dict, tier: int) -> dict:
        items, snippets = self._extract_all_data(results)
        return {
            "status": "consent_required",
            "items": items,
            "snippets": snippets,
            "sources_used": [k for k, v in results.items() if v.get("status") == "success"],
            "consent_prompt": {
                "type": metadata.get("consent_type"),
                "message": metadata.get("message"),
                "next_tier": metadata.get("next_tier"),
            },
            "tier_reached": tier,
        }

    def _build_partial_response(self, results: dict, metadata: dict, tier: int) -> dict:
        items, snippets = self._extract_all_data(results)
        return {
            "status": "partial",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get("sources_used", [k for k, v in results.items() if v.get("status") == "success"]),
            "message": metadata.get("message", "Showing results from available sources"),
            "tier_reached": tier,
        }

    def _extract_all_data(self, results: dict) -> tuple[list, list]:
        items = []
        snippets = []
        seen_items = set()

        for api_result in results.values():
            if api_result.get("status") != "success":
                continue
            data = api_result.get("data", {})

            for item in data.get("products", []) + data.get("hotels", []) + data.get("flights", []):
                item_key = self._get_item_key(item)
                if item_key not in seen_items:
                    seen_items.add(item_key)
                    items.append(item)

            snippets.extend(data.get("snippets", []))

        return items, snippets

    def _get_item_key(self, item: dict) -> tuple:
        return (item.get("name", "").lower(), item.get("price"))
```

---

## 8. Workflow Integration

### Routing Gate Node

```python
# backend/app/services/langgraph/nodes/routing_gate.py

DETERMINISTIC_INTENTS = {"product", "comparison", "price_check", "travel", "review_deep_dive"}

async def routing_gate_node(state: GraphState) -> GraphState:
    intent = state.get("intent")

    if intent in DETERMINISTIC_INTENTS:
        return {
            **state,
            "routing_mode": "tiered",
            "next_agent": "tiered_executor",
        }
    else:
        return {
            **state,
            "routing_mode": "llm",
            "next_agent": "planner",
        }
```

### Tiered Executor Node

```python
# backend/app/services/langgraph/nodes/tiered_executor.py

orchestrator = TieredAPIOrchestrator()

async def tiered_executor_node(state: GraphState) -> GraphState:
    intent = state.get("intent")
    query = state.get("user_message")

    result = await orchestrator.execute(intent, query, state)

    if result["status"] == "consent_required":
        return {
            **state,
            "status": "halted",
            "halt_reason": "consent_required",
            "consent_prompt": result["consent_prompt"],
            "partial_items": result["items"],
            "partial_snippets": result["snippets"],
            "tier_reached": result["tier_reached"],
            "next_agent": None,
        }

    return {
        **state,
        "tier_results": result,
        "search_results": result["items"],
        "snippets": result["snippets"],
        "sources_used": result["sources_used"],
        "sources_unavailable": result.get("sources_unavailable", []),
        "next_agent": "synthesizer",
    }
```

### Updated Workflow Graph

```python
def build_workflow() -> StateGraph:
    workflow = StateGraph(GraphState)

    # Existing nodes
    workflow.add_node("safety", safety_agent_node)
    workflow.add_node("intent", intent_agent_node)
    workflow.add_node("clarifier", clarifier_agent_node)
    workflow.add_node("planner", planner_agent_node)
    workflow.add_node("plan_executor", plan_executor_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # New nodes
    workflow.add_node("routing_gate", routing_gate_node)
    workflow.add_node("tiered_executor", tiered_executor_node)

    # Flow
    workflow.set_entry_point("safety")
    workflow.add_edge("safety", "intent")
    workflow.add_edge("intent", "clarifier")  # Always clarify first
    workflow.add_edge("clarifier", "routing_gate")

    # Conditional routing
    workflow.add_conditional_edges(
        "routing_gate",
        lambda s: s.get("next_agent"),
        {
            "tiered_executor": "tiered_executor",
            "planner": "planner",
        }
    )

    # Tiered path
    workflow.add_conditional_edges(
        "tiered_executor",
        lambda s: s.get("next_agent") if s.get("status") != "halted" else END,
        {
            "synthesizer": "synthesizer",
            None: END,
        }
    )

    # LLM path
    workflow.add_edge("planner", "plan_executor")
    workflow.add_edge("plan_executor", "synthesizer")

    workflow.add_edge("synthesizer", END)

    return workflow.compile()
```

### Resume Flow (Chat Endpoint)

```python
# backend/app/api/v1/chat.py

def is_consent_confirmation(request: ChatRequest) -> bool:
    if getattr(request, "action", None) == "consent_confirm":
        return True
    if request.message:
        consent_patterns = {"yes", "search deeper", "continue", "ok", "proceed", "go ahead"}
        normalized = request.message.strip().lower()
        return normalized in consent_patterns or normalized.startswith("yes")
    return False

async def handle_message(request: ChatRequest, session_id: str):
    halt_state = await HaltStateManager.get(session_id)

    if halt_state and halt_state.halt_reason == "consent_required":
        if is_consent_confirmation(request):
            state = halt_state.saved_state
            state["extended_search_confirmed"] = True
            await HaltStateManager.clear(session_id)

            # Resume at tiered_executor, skip Safety (consent msg is trusted)
            return await workflow.ainvoke(
                state,
                config={"configurable": {"start_at": "tiered_executor"}}
            )
        else:
            # User said something else - treat as new query
            await HaltStateManager.clear(session_id)

    # Normal flow
    return await workflow.ainvoke({"user_message": request.message, ...})
```

---

## 9. GraphState Changes

### New Fields

```python
class GraphState(TypedDict, total=False):
    # ... existing fields ...

    # --- Routing Decision ---
    routing_mode: Literal["tiered", "llm"]

    # --- User Context ---
    user_id: str
    user_extended_search_enabled: bool  # Account-level toggle

    # --- Tier Execution State ---
    current_tier: int
    tier_results: Dict  # Full orchestrator output

    # --- Consent Flow ---
    extended_search_confirmed: bool  # Per-query consent
    consent_prompt: Dict  # {type, message, next_tier}

    # --- Partial Results ---
    partial_items: List[Dict]  # Items before consent halt
    partial_snippets: List[Dict]

    # --- Source Attribution ---
    sources_used: List[str]  # APIs that returned data
    sources_unavailable: List[str]  # APIs that failed

    # --- Debugging ---
    tier_api_calls: List[Dict]  # Request-scoped API call log

    # --- Comparison-Specific ---
    requested_products: List[str]  # Products user asked to compare
    # (Distinct from product_names which are products FOUND in results)
```

---

## 10. Database Changes

### New Table: api_usage_logs

```sql
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id UUID,
    api_name VARCHAR(50) NOT NULL,
    tier SMALLINT NOT NULL,
    cost_cents INTEGER NOT NULL,
    latency_ms INTEGER,
    success BOOLEAN NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_usage_user_month ON api_usage_logs (user_id, created_at);
CREATE INDEX idx_api_usage_api_name ON api_usage_logs (api_name, created_at);
```

### User Model Addition

```python
class User(Base):
    # ... existing fields ...
    extended_search_enabled: bool = Column(Boolean, default=False)
```

---

## 11. Feature Flags

Add to `backend/app/core/config.py`:

```python
# Tiered routing flags
ENABLE_SERPAPI: bool = False  # Tier 4 - HIGH LEGAL RISK
ENABLE_REDDIT_API: bool = False  # Tier 3 - Requires commercial license
ENABLE_YOUTUBE_TRANSCRIPTS: bool = True  # Tier 2
MAX_AUTO_TIER: int = 2  # Highest tier to auto-escalate to
PARALLEL_API_TIMEOUT_MS: int = 5000  # Timeout per API call
LOG_API_COSTS: bool = True  # Track API usage costs
```

---

## 12. Implementation Order

1. **Database migrations** - Add `api_usage_logs` table, `extended_search_enabled` to User
2. **API Registry** - Define all API configs
3. **Circuit Breaker** - Module-level singleton
4. **Parallel Fetcher** - With cost logging
5. **Data Validator** - Threshold checking
6. **Tiered Router** - Routing table lookup
7. **Orchestrator** - Main coordinator
8. **LangGraph nodes** - routing_gate, tiered_executor
9. **Workflow integration** - Update graph definition
10. **Chat endpoint** - Resume flow for consent
11. **Frontend** - Consent UI (separate spec)

---

## 13. Testing Strategy

### Unit Tests

- Router: Correct APIs returned per intent/tier
- Validator: Threshold logic, consent gating
- Circuit Breaker: Opens after failures, resets after timeout

### Integration Tests

- Full flow: product query → Tier 1 → sufficient → response
- Escalation: product query → Tier 1 insufficient → Tier 2 → sufficient
- Consent flow: Tier 2 insufficient → halt → resume → Tier 3 → response
- Graceful degradation: API timeout → partial results

### Load Tests

- Confirm < 2s response time at p95
- Verify circuit breaker prevents cascade failures

---

## 14. Open Questions

1. **LangGraph `start_at` syntax** - Verify correct config key for your version
2. **Frontend consent UI** - Button placement, partial results display (separate spec)
3. **Cost alerting** - Threshold for API spend alerts (implementation detail)

---

*Document generated from design session, 2026-01-31*
