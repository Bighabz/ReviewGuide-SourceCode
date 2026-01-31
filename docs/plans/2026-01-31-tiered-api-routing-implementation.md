# Tiered API Routing - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a legally compliant, tiered API routing system that uses deterministic rules for common intents and falls back to LLM planner for ambiguous queries.

**Architecture:** Hybrid routing with 4-tier API escalation. Tier 1-2 auto-escalate based on count thresholds. Tier 3-4 require explicit two-layer user consent (account toggle + per-query confirmation). Circuit breaker prevents cascade failures.

**Tech Stack:** FastAPI, LangGraph, PostgreSQL, Redis, asyncio, Pydantic

**Design Document:** [2026-01-31-tiered-api-routing-design.md](./2026-01-31-tiered-api-routing-design.md)

---

## Task 1: Database Migration - api_usage_logs Table

**Files:**
- Create: `backend/alembic/versions/20260131_0001_add_api_usage_logs.py`
- Reference: `backend/alembic/versions/20251202_2221_ea3fb8398a5a_create_admin_users_table.py` (pattern)

**Step 1: Write the migration file**

```python
"""Add api_usage_logs table for cost tracking

Revision ID: 20260131_0001
Revises: ea3fb8398a5a
Create Date: 2026-01-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260131_0001"
down_revision = "ea3fb8398a5a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_usage_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("api_name", sa.String(50), nullable=False),
        sa.Column("tier", sa.SmallInteger, nullable=False),
        sa.Column("cost_cents", sa.Integer, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_api_usage_user_month", "api_usage_logs", ["user_id", "created_at"])
    op.create_index("idx_api_usage_api_name", "api_usage_logs", ["api_name", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_api_usage_api_name", table_name="api_usage_logs")
    op.drop_index("idx_api_usage_user_month", table_name="api_usage_logs")
    op.drop_table("api_usage_logs")
```

**Step 2: Run migration to verify it works**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully

**Step 3: Commit**

```bash
git add backend/alembic/versions/20260131_0001_add_api_usage_logs.py
git commit -m "feat(db): add api_usage_logs table for cost tracking"
```

---

## Task 2: Database Migration - User extended_search_enabled Field

**Files:**
- Create: `backend/alembic/versions/20260131_0002_add_user_extended_search.py`
- Modify: `backend/app/models/user.py`

**Step 1: Write the migration file**

```python
"""Add extended_search_enabled to users table

Revision ID: 20260131_0002
Revises: 20260131_0001
Create Date: 2026-01-31
"""
from alembic import op
import sqlalchemy as sa

revision = "20260131_0002"
down_revision = "20260131_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("extended_search_enabled", sa.Boolean, server_default=sa.text("FALSE"), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("users", "extended_search_enabled")
```

**Step 2: Update User model**

In `backend/app/models/user.py`, add:

```python
extended_search_enabled = Column(Boolean, default=False, nullable=False)
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Column added successfully

**Step 4: Commit**

```bash
git add backend/alembic/versions/20260131_0002_add_user_extended_search.py backend/app/models/user.py
git commit -m "feat(db): add extended_search_enabled to users for Tier 3-4 consent"
```

---

## Task 3: Feature Flags Configuration

**Files:**
- Modify: `backend/app/core/config.py`

**Step 1: Add feature flags to Settings class**

In `backend/app/core/config.py`, add to the Settings class (after existing search settings):

```python
# ============================================
# TIERED ROUTING CONFIGURATION
# ============================================

# Feature flags for high-risk APIs
ENABLE_SERPAPI: bool = Field(
    default=False,
    description="Enable SerpApi (Tier 4) - HIGH LEGAL RISK, requires user consent"
)
ENABLE_REDDIT_API: bool = Field(
    default=False,
    description="Enable Reddit API (Tier 3) - Requires commercial license and user consent"
)
ENABLE_YOUTUBE_TRANSCRIPTS: bool = Field(
    default=True,
    description="Enable YouTube transcript extraction (Tier 2)"
)

# Tier escalation settings
MAX_AUTO_TIER: int = Field(
    default=2,
    ge=1,
    le=4,
    description="Highest tier to auto-escalate to without user consent (1-4)"
)
PARALLEL_API_TIMEOUT_MS: int = Field(
    default=5000,
    ge=1000,
    le=30000,
    description="Timeout per API call in milliseconds"
)

# Cost tracking
LOG_API_COSTS: bool = Field(
    default=True,
    description="Track API usage costs in api_usage_logs table"
)

# Circuit breaker settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(
    default=3,
    ge=1,
    le=10,
    description="Number of failures before opening circuit"
)
CIRCUIT_BREAKER_RESET_TIMEOUT: int = Field(
    default=300,
    ge=60,
    le=3600,
    description="Seconds before attempting to close circuit"
)
```

**Step 2: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat(config): add tiered routing feature flags"
```

---

## Task 4: API Registry Module

**Files:**
- Create: `backend/app/services/tiered_router/__init__.py`
- Create: `backend/app/services/tiered_router/api_registry.py`
- Test: `backend/tests/test_tiered_router/test_api_registry.py`

**Step 1: Create directory and __init__.py**

```python
# backend/app/services/tiered_router/__init__.py
"""Tiered API Routing System

Provides deterministic, rule-based API routing for product, travel, price,
and comparison intents with 4-tier escalation and two-layer consent.
"""
```

**Step 2: Write the failing test**

```python
# backend/tests/test_tiered_router/test_api_registry.py
import pytest
from app.services.tiered_router.api_registry import APIConfig, API_REGISTRY


def test_api_config_has_required_fields():
    """APIConfig should have all required fields"""
    config = APIConfig(
        name="test_api",
        mcp_tool="product_search",
        provider="test",
        cost_cents=5,
    )
    assert config.name == "test_api"
    assert config.mcp_tool == "product_search"
    assert config.provider == "test"
    assert config.cost_cents == 5
    assert config.timeout_ms == 5000  # default
    assert config.requires_consent is False  # default
    assert config.feature_flag is None  # default


def test_api_registry_contains_tier_1_affiliates():
    """Registry should contain Tier 1 affiliate APIs"""
    tier_1_apis = ["amazon_affiliate", "walmart_affiliate", "bestbuy_affiliate", "ebay_affiliate"]
    for api in tier_1_apis:
        assert api in API_REGISTRY
        assert API_REGISTRY[api].cost_cents == 0  # Affiliates are free


def test_api_registry_tier_3_4_require_consent():
    """Tier 3-4 APIs should require consent"""
    assert API_REGISTRY["reddit_api"].requires_consent is True
    assert API_REGISTRY["serpapi"].requires_consent is True


def test_api_registry_tier_3_4_have_feature_flags():
    """Tier 3-4 APIs should have feature flags"""
    assert API_REGISTRY["reddit_api"].feature_flag == "ENABLE_REDDIT_API"
    assert API_REGISTRY["serpapi"].feature_flag == "ENABLE_SERPAPI"
```

**Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_api_registry.py -v`
Expected: FAIL - module not found

**Step 4: Write the implementation**

```python
# backend/app/services/tiered_router/api_registry.py
"""API Registry - Maps logical API names to implementation details."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class APIConfig:
    """Configuration for a single API endpoint.

    Attributes:
        name: Logical name used in routing table
        mcp_tool: MCP tool name to execute
        provider: Provider key passed to MCP tool
        cost_cents: Cost per call in cents (0 for affiliates)
        timeout_ms: Request timeout in milliseconds
        requires_consent: Whether Tier 3-4 consent is needed
        feature_flag: Config flag that must be enabled (e.g., ENABLE_SERPAPI)
    """
    name: str
    mcp_tool: str
    provider: str
    cost_cents: int
    timeout_ms: int = 5000
    requires_consent: bool = False
    feature_flag: Optional[str] = None


API_REGISTRY: dict[str, APIConfig] = {
    # ============================================
    # TIER 1 - Affiliates (free, revenue share)
    # ============================================
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

    # ============================================
    # TIER 1 - Search (low cost)
    # ============================================
    "google_cse_product": APIConfig(
        name="google_cse_product",
        mcp_tool="product_search",
        provider="google_cse",
        cost_cents=1,
    ),
    "google_cse_travel": APIConfig(
        name="google_cse_travel",
        mcp_tool="travel_search",
        provider="google_cse",
        cost_cents=1,
    ),

    # ============================================
    # TIER 2 - Extended search
    # ============================================
    "bing_search": APIConfig(
        name="bing_search",
        mcp_tool="product_search",
        provider="bing",
        cost_cents=1,
    ),
    "youtube_transcripts": APIConfig(
        name="youtube_transcripts",
        mcp_tool="product_evidence",
        provider="youtube",
        cost_cents=0,
        feature_flag="ENABLE_YOUTUBE_TRANSCRIPTS",
    ),
    "google_shopping": APIConfig(
        name="google_shopping",
        mcp_tool="product_search",
        provider="google_shopping",
        cost_cents=1,
    ),

    # ============================================
    # TIER 3 - Consent required
    # ============================================
    "reddit_api": APIConfig(
        name="reddit_api",
        mcp_tool="product_evidence",
        provider="reddit",
        cost_cents=1,
        requires_consent=True,
        feature_flag="ENABLE_REDDIT_API",
    ),

    # ============================================
    # TIER 4 - High risk, consent required
    # ============================================
    "serpapi": APIConfig(
        name="serpapi",
        mcp_tool="product_search",
        provider="serpapi",
        cost_cents=1,
        requires_consent=True,
        feature_flag="ENABLE_SERPAPI",
    ),

    # ============================================
    # TRAVEL APIs
    # ============================================
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


def get_api_config(api_name: str) -> Optional[APIConfig]:
    """Get API configuration by name."""
    return API_REGISTRY.get(api_name)
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_api_registry.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/tiered_router/ backend/tests/test_tiered_router/
git commit -m "feat(tiered-router): add API registry with configs for all tiers"
```

---

## Task 5: Tiered Router Module

**Files:**
- Create: `backend/app/services/tiered_router/router.py`
- Test: `backend/tests/test_tiered_router/test_router.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_router.py
import pytest
from unittest.mock import MagicMock
from app.services.tiered_router.router import (
    TIER_ROUTING_TABLE,
    get_apis_for_tier,
    UnknownIntentError,
)


def test_tier_routing_table_has_product_intent():
    """Routing table should have product intent with 4 tiers"""
    assert "product" in TIER_ROUTING_TABLE
    assert 1 in TIER_ROUTING_TABLE["product"]
    assert 4 in TIER_ROUTING_TABLE["product"]


def test_tier_1_product_has_affiliates():
    """Product Tier 1 should have affiliate APIs"""
    tier_1 = TIER_ROUTING_TABLE["product"][1]
    assert "amazon_affiliate" in tier_1
    assert "walmart_affiliate" in tier_1


def test_tier_3_product_has_reddit():
    """Product Tier 3 should have reddit_api"""
    tier_3 = TIER_ROUTING_TABLE["product"][3]
    assert "reddit_api" in tier_3


def test_get_apis_for_tier_returns_apis():
    """get_apis_for_tier should return list of APIs"""
    mock_cb = MagicMock()
    mock_cb.is_open.return_value = False

    apis = get_apis_for_tier("product", 1, mock_cb)

    assert isinstance(apis, list)
    assert len(apis) > 0
    assert "amazon_affiliate" in apis


def test_get_apis_for_tier_filters_circuit_broken():
    """get_apis_for_tier should filter out circuit-broken APIs"""
    mock_cb = MagicMock()
    mock_cb.is_open.side_effect = lambda api: api == "amazon_affiliate"

    apis = get_apis_for_tier("product", 1, mock_cb)

    assert "amazon_affiliate" not in apis


def test_get_apis_for_tier_unknown_intent_raises():
    """get_apis_for_tier should raise for unknown intent"""
    mock_cb = MagicMock()
    mock_cb.is_open.return_value = False

    with pytest.raises(UnknownIntentError):
        get_apis_for_tier("invalid_intent", 1, mock_cb)


def test_price_check_has_no_tier_3_4():
    """price_check should have empty Tier 3-4"""
    assert TIER_ROUTING_TABLE["price_check"][3] == []
    assert TIER_ROUTING_TABLE["price_check"][4] == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_router.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/tiered_router/router.py
"""Tiered API Router - Deterministic routing table lookup."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .circuit_breaker import CircuitBreaker


class UnknownIntentError(Exception):
    """Raised when intent has no routing rules defined."""
    pass


# Routing table: intent -> tier -> list of API names
TIER_ROUTING_TABLE: dict[str, dict[int, list[str]]] = {
    "product": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
            "google_cse_product",
        ],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "comparison": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
            "google_cse_product",
        ],
        2: ["bing_search", "youtube_transcripts"],
        3: ["reddit_api"],
        4: ["serpapi"],
    },
    "price_check": {
        1: [
            "amazon_affiliate",
            "walmart_affiliate",
            "bestbuy_affiliate",
            "ebay_affiliate",
        ],
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


def get_apis_for_tier(
    intent: str,
    tier: int,
    circuit_breaker: "CircuitBreaker",
) -> list[str]:
    """Get available APIs for a given intent and tier.

    Args:
        intent: The classified intent (product, comparison, etc.)
        tier: The tier level (1-4)
        circuit_breaker: CircuitBreaker instance to filter unavailable APIs

    Returns:
        List of API names available for this tier

    Raises:
        UnknownIntentError: If intent has no routing rules
    """
    if intent not in TIER_ROUTING_TABLE:
        raise UnknownIntentError(f"No routing rules for intent: {intent}")

    apis = TIER_ROUTING_TABLE.get(intent, {}).get(tier, [])

    # Filter out circuit-broken APIs
    return [api for api in apis if not circuit_breaker.is_open(api)]
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_router.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/tiered_router/router.py backend/tests/test_tiered_router/test_router.py
git commit -m "feat(tiered-router): add routing table with intent-to-API mapping"
```

---

## Task 6: Circuit Breaker Module

**Files:**
- Create: `backend/app/services/tiered_router/circuit_breaker.py`
- Test: `backend/tests/test_tiered_router/test_circuit_breaker.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_circuit_breaker.py
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.services.tiered_router.circuit_breaker import CircuitBreaker


def test_circuit_breaker_starts_closed():
    """New circuit breaker should have all circuits closed"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)
    assert cb.is_open("any_api") is False


def test_circuit_opens_after_threshold_failures():
    """Circuit should open after reaching failure threshold"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)

    cb.record_failure("test_api")
    cb.record_failure("test_api")
    assert cb.is_open("test_api") is False

    cb.record_failure("test_api")  # 3rd failure
    assert cb.is_open("test_api") is True


def test_circuit_resets_on_success():
    """Recording success should reset failure count"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)

    cb.record_failure("test_api")
    cb.record_failure("test_api")
    cb.record_success("test_api")

    assert cb.is_open("test_api") is False

    # Should need 3 more failures to open
    cb.record_failure("test_api")
    cb.record_failure("test_api")
    assert cb.is_open("test_api") is False


def test_circuit_closes_after_timeout():
    """Open circuit should close after reset timeout"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)

    # Open the circuit
    for _ in range(3):
        cb.record_failure("test_api")
    assert cb.is_open("test_api") is True

    # Mock time to be past reset timeout
    future_time = datetime.now(timezone.utc) + timedelta(seconds=301)
    with patch("app.services.tiered_router.circuit_breaker.datetime") as mock_dt:
        mock_dt.now.return_value = future_time
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        assert cb.is_open("test_api") is False


def test_circuit_isolation():
    """Failures on one API should not affect another"""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)

    for _ in range(3):
        cb.record_failure("api_a")

    assert cb.is_open("api_a") is True
    assert cb.is_open("api_b") is False
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_circuit_breaker.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/tiered_router/circuit_breaker.py
"""Circuit Breaker - Skip APIs that have failed repeatedly.

States: CLOSED (normal) → OPEN (skip) → CLOSED (after timeout)

TODO: If scaling beyond 3 workers, consider Redis-backed state
to share failure state across workers.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.config import settings


class CircuitBreaker:
    """Skip APIs that have failed repeatedly.

    Args:
        failure_threshold: Number of failures before opening circuit
        reset_timeout: Seconds before attempting to close circuit
    """

    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        reset_timeout: Optional[int] = None,
    ):
        self.failure_threshold = failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.reset_timeout = reset_timeout or settings.CIRCUIT_BREAKER_RESET_TIMEOUT
        self._state: dict[str, dict] = {}

    def is_open(self, api_name: str) -> bool:
        """Check if circuit is open (should skip this API).

        Returns:
            True if circuit is open (API should be skipped)
            False if circuit is closed (API can be called)
        """
        state = self._state.get(api_name)
        if not state:
            return False

        open_until = state.get("open_until")
        if not open_until:
            return False

        now = datetime.now(timezone.utc)
        if now < open_until:
            return True

        # Reset after timeout
        self._state[api_name] = {"failures": 0, "open_until": None}
        return False

    def record_failure(self, api_name: str) -> None:
        """Record a failure for an API.

        Opens circuit after failure_threshold consecutive failures.
        """
        state = self._state.setdefault(api_name, {"failures": 0, "open_until": None})
        state["failures"] += 1

        if state["failures"] >= self.failure_threshold:
            state["open_until"] = datetime.now(timezone.utc) + timedelta(seconds=self.reset_timeout)

    def record_success(self, api_name: str) -> None:
        """Record a success for an API. Resets failure count."""
        self._state[api_name] = {"failures": 0, "open_until": None}


# Module-level singleton for production use
_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get or create the circuit breaker singleton."""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_circuit_breaker.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/tiered_router/circuit_breaker.py backend/tests/test_tiered_router/test_circuit_breaker.py
git commit -m "feat(tiered-router): add circuit breaker for graceful degradation"
```

---

## Task 7: Data Validator Module

**Files:**
- Create: `backend/app/services/tiered_router/data_validator.py`
- Test: `backend/tests/test_tiered_router/test_data_validator.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_data_validator.py
import pytest
from app.services.tiered_router.data_validator import (
    DataValidator,
    ValidationResult,
    ThresholdConfig,
    INTENT_THRESHOLDS,
)


@pytest.fixture
def validator():
    return DataValidator(max_auto_tier=2)


def test_sufficient_product_results(validator):
    """3+ products should be sufficient for product intent"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "p1"}, {"name": "p2"}, {"name": "p3"}]}},
    }

    result, metadata = validator.validate("product", 1, results)

    assert result == ValidationResult.SUFFICIENT
    assert metadata["item_count"] == 3


def test_insufficient_product_escalates(validator):
    """< 3 products should escalate to next tier"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "p1"}, {"name": "p2"}]}},
    }

    result, metadata = validator.validate("product", 1, results)

    assert result == ValidationResult.ESCALATE
    assert metadata["next_tier"] == 2


def test_tier_3_requires_consent(validator):
    """Tier 3 escalation should require consent"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": False})

    assert result == ValidationResult.CONSENT_REQUIRED
    assert metadata["consent_type"] == "account_toggle"


def test_tier_3_with_account_toggle_requires_per_query(validator):
    """Account toggle enabled should still require per-query consent"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": True, "per_query": False})

    assert result == ValidationResult.CONSENT_REQUIRED
    assert metadata["consent_type"] == "per_query"


def test_tier_3_with_full_consent_escalates(validator):
    """Full consent should allow Tier 3 escalation"""
    results = {
        "bing": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate("product", 2, results, user_consent={"account_toggle": True, "per_query": True})

    assert result == ValidationResult.ESCALATE
    assert metadata["next_tier"] == 3


def test_comparison_requires_all_products(validator):
    """Comparison intent should require all requested products"""
    results = {
        "amazon": {"status": "success", "data": {"products": [{"name": "Dyson V15"}]}},
    }

    result, metadata = validator.validate(
        "comparison", 1, results,
        requested_products=["Dyson V15", "Shark Navigator"]
    )

    assert result == ValidationResult.ESCALATE  # Missing Shark


def test_comparison_sufficient_with_all_products(validator):
    """Comparison with all products should be sufficient"""
    results = {
        "amazon": {"status": "success", "data": {"products": [
            {"name": "Dyson V15 Detect"},
            {"name": "Shark Navigator Lift-Away"},
        ]}},
    }

    result, metadata = validator.validate(
        "comparison", 1, results,
        requested_products=["Dyson V15", "Shark Navigator"]
    )

    assert result == ValidationResult.SUFFICIENT


def test_max_tier_reached(validator):
    """Tier 4 exhausted should return MAX_TIER_REACHED"""
    results = {
        "serpapi": {"status": "success", "data": {"products": [{"name": "p1"}]}},
    }

    result, metadata = validator.validate(
        "product", 4, results,
        user_consent={"account_toggle": True, "per_query": True}
    )

    assert result == ValidationResult.MAX_TIER_REACHED
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_data_validator.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/tiered_router/data_validator.py
"""Data Validator - Check thresholds and decide on tier escalation."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ValidationResult(Enum):
    """Possible outcomes of data validation."""
    SUFFICIENT = "sufficient"
    ESCALATE = "escalate"
    CONSENT_REQUIRED = "consent_required"
    MAX_TIER_REACHED = "max_tier_reached"


@dataclass
class ThresholdConfig:
    """Threshold configuration for an intent type.

    Attributes:
        min_items: Minimum products/hotels/flights required
        min_snippets: Minimum review snippets required
        min_sources: Minimum unique sources required
        require_all_items: For comparison - must have all requested items
    """
    min_items: int = 0
    min_snippets: int = 0
    min_sources: int = 0
    require_all_items: bool = False


INTENT_THRESHOLDS: dict[str, ThresholdConfig] = {
    "product": ThresholdConfig(min_items=3),
    "comparison": ThresholdConfig(require_all_items=True),
    "price_check": ThresholdConfig(min_items=1),
    "review_deep_dive": ThresholdConfig(min_snippets=5, min_sources=2),
    "travel": ThresholdConfig(min_items=1, min_snippets=3),
}


class DataValidator:
    """Validate tier results and decide on escalation.

    Args:
        max_auto_tier: Highest tier that can auto-escalate without consent (1-2)
    """

    def __init__(self, max_auto_tier: int = 2):
        self.max_auto_tier = max_auto_tier

    def validate(
        self,
        intent: str,
        current_tier: int,
        results: dict[str, dict],
        requested_products: Optional[list[str]] = None,
        user_consent: Optional[dict] = None,
    ) -> tuple[ValidationResult, dict]:
        """Validate results and determine next action.

        Args:
            intent: The classified intent type
            current_tier: Current tier level (1-4)
            results: Dict of API results keyed by API name
            requested_products: For comparison - specific products to find
            user_consent: {"account_toggle": bool, "per_query": bool}

        Returns:
            Tuple of (ValidationResult, metadata dict)
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

        # Auto-escalate within allowed tiers
        if next_tier <= self.max_auto_tier:
            return ValidationResult.ESCALATE, {"next_tier": next_tier}

        # Tier 3-4 requires consent
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

        # All tiers exhausted
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
        requested_products: Optional[list[str]] = None,
        sources_used: Optional[list[str]] = None,
    ) -> bool:
        """Check if results meet threshold requirements."""
        if threshold.require_all_items:
            if not requested_products:
                return len(items) >= 2  # Default: need at least 2 for comparison
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
        """Extract all items (products, hotels, flights) from results."""
        items = []
        for api_result in results.values():
            data = api_result.get("data", {})
            items.extend(data.get("products", []))
            items.extend(data.get("hotels", []))
            items.extend(data.get("flights", []))
        return items

    def _extract_snippets(self, results: dict) -> list:
        """Extract all review snippets from results."""
        snippets = []
        for api_result in results.values():
            data = api_result.get("data", {})
            snippets.extend(data.get("snippets", []))
        return snippets
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_data_validator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/tiered_router/data_validator.py backend/tests/test_tiered_router/test_data_validator.py
git commit -m "feat(tiered-router): add data validator with threshold checking and consent gating"
```

---

## Task 8: API Usage Logger

**Files:**
- Create: `backend/app/services/tiered_router/api_logger.py`
- Create: `backend/app/models/api_usage_log.py`
- Test: `backend/tests/test_tiered_router/test_api_logger.py`

**Step 1: Write the SQLAlchemy model**

```python
# backend/app/models/api_usage_log.py
"""API Usage Log model for cost tracking."""

from sqlalchemy import Column, String, Integer, SmallInteger, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class APIUsageLog(Base):
    """Tracks API call costs and outcomes."""

    __tablename__ = "api_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    api_name = Column(String(50), nullable=False)
    tier = Column(SmallInteger, nullable=False)
    cost_cents = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

**Step 2: Write the failing test**

```python
# backend/tests/test_tiered_router/test_api_logger.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tiered_router.api_logger import log_api_usage, log_consent_event


@pytest.mark.asyncio
async def test_log_api_usage_creates_record():
    """log_api_usage should create a database record"""
    mock_session = AsyncMock()

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_session):
        await log_api_usage(
            user_id="test-user-id",
            session_id="test-session",
            api_name="amazon_affiliate",
            tier=1,
            cost_cents=0,
            latency_ms=234,
            success=True,
        )

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_api_usage_handles_error():
    """log_api_usage should log error field on failure"""
    mock_session = AsyncMock()

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_session):
        await log_api_usage(
            user_id="test-user-id",
            session_id="test-session",
            api_name="bestbuy_affiliate",
            tier=1,
            cost_cents=0,
            latency_ms=5000,
            success=False,
            error="timeout",
        )

    call_args = mock_session.add.call_args[0][0]
    assert call_args.success is False
    assert call_args.error == "timeout"


@pytest.mark.asyncio
async def test_log_consent_event():
    """log_consent_event should create a consent record"""
    mock_session = AsyncMock()

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_session):
        await log_consent_event(
            user_id="test-user-id",
            session_id="test-session",
            consent_type="per_query",
            tier_requested=3,
        )

    mock_session.add.assert_called_once()
```

**Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_api_logger.py -v`
Expected: FAIL - module not found

**Step 4: Write the implementation**

```python
# backend/app/services/tiered_router/api_logger.py
"""API Usage Logger - Track API costs and consent events."""

import logging
from typing import Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.api_usage_log import APIUsageLog

logger = logging.getLogger(__name__)


async def log_api_usage(
    user_id: Optional[str],
    session_id: Optional[str],
    api_name: str,
    tier: int,
    cost_cents: int,
    latency_ms: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Log an API call to the database.

    Args:
        user_id: User ID (optional for anonymous users)
        session_id: Chat session ID
        api_name: Name of the API called
        tier: Tier level (1-4)
        cost_cents: Cost in cents
        latency_ms: Response time in milliseconds
        success: Whether the call succeeded
        error: Error message if failed
    """
    if not settings.LOG_API_COSTS:
        return

    try:
        async with AsyncSessionLocal() as session:
            log_entry = APIUsageLog(
                user_id=user_id,
                session_id=session_id,
                api_name=api_name,
                tier=tier,
                cost_cents=cost_cents,
                latency_ms=latency_ms,
                success=success,
                error=error,
            )
            session.add(log_entry)
            await session.commit()
    except Exception as e:
        # Don't fail the request if logging fails
        logger.warning(f"Failed to log API usage: {e}")


async def log_consent_event(
    user_id: str,
    session_id: str,
    consent_type: str,
    tier_requested: int,
) -> None:
    """Log a consent event for compliance tracking.

    This creates a special API log entry with api_name="consent_{type}"
    to create an audit trail of user consent actions.
    """
    await log_api_usage(
        user_id=user_id,
        session_id=session_id,
        api_name=f"consent_{consent_type}",
        tier=tier_requested,
        cost_cents=0,
        success=True,
    )
    logger.info(f"Consent logged: user={user_id}, type={consent_type}, tier={tier_requested}")
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_api_logger.py -v`
Expected: PASS

**Step 6: Add model to models/__init__.py**

In `backend/app/models/__init__.py`, add:
```python
from .api_usage_log import APIUsageLog
```

**Step 7: Commit**

```bash
git add backend/app/services/tiered_router/api_logger.py backend/app/models/api_usage_log.py backend/tests/test_tiered_router/test_api_logger.py
git commit -m "feat(tiered-router): add API usage logger for cost tracking"
```

---

## Task 9: Parallel Fetcher Module

**Files:**
- Create: `backend/app/services/tiered_router/parallel_fetcher.py`
- Test: `backend/tests/test_tiered_router/test_parallel_fetcher.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_parallel_fetcher.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tiered_router.parallel_fetcher import ParallelFetcher
from app.services.tiered_router.circuit_breaker import CircuitBreaker


@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(failure_threshold=3, reset_timeout=300)


@pytest.fixture
def fetcher(circuit_breaker):
    return ParallelFetcher(circuit_breaker)


@pytest.mark.asyncio
async def test_fetch_tier_returns_results(fetcher):
    """fetch_tier should return results from all APIs"""
    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"status": "success", "api": "test", "data": {"products": []}}

        results = await fetcher.fetch_tier(["amazon_affiliate", "walmart_affiliate"], "test query", mock_state)

    assert "amazon_affiliate" in results
    assert "walmart_affiliate" in results


@pytest.mark.asyncio
async def test_fetch_tier_marks_circuit_open(fetcher, circuit_breaker):
    """fetch_tier should mark circuit-broken APIs"""
    # Open circuit for amazon
    for _ in range(3):
        circuit_breaker.record_failure("amazon_affiliate")

    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"status": "success", "api": "test", "data": {}}

        results = await fetcher.fetch_tier(["amazon_affiliate", "walmart_affiliate"], "test query", mock_state)

    assert results["amazon_affiliate"]["status"] == "circuit_open"
    assert results["walmart_affiliate"]["status"] == "success"


@pytest.mark.asyncio
async def test_fetch_tier_handles_timeout(fetcher, circuit_breaker):
    """fetch_tier should handle timeouts gracefully"""
    mock_state = {"user_id": "test", "session_id": "sess"}

    async def slow_fetch(*args, **kwargs):
        await asyncio.sleep(10)  # Longer than timeout

    with patch.object(fetcher, "_fetch_single", side_effect=asyncio.TimeoutError):
        with patch("app.services.tiered_router.parallel_fetcher.log_api_usage", new_callable=AsyncMock):
            results = await fetcher.fetch_tier(["amazon_affiliate"], "test query", mock_state)

    # Should handle the exception from gather
    assert "amazon_affiliate" in results


@pytest.mark.asyncio
async def test_fetch_tier_runs_in_parallel(fetcher):
    """fetch_tier should call APIs in parallel, not sequentially"""
    call_times = []

    async def track_call(api, query, state):
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)
        return {"status": "success", "api": api, "data": {}}

    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", side_effect=track_call):
        await fetcher.fetch_tier(["api1", "api2", "api3"], "test query", mock_state)

    # If parallel, all calls should start within 0.05s of each other
    assert len(call_times) == 3
    assert max(call_times) - min(call_times) < 0.05
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_parallel_fetcher.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/tiered_router/parallel_fetcher.py
"""Parallel Fetcher - Concurrent API calls with circuit breaker."""

import asyncio
import time
import logging
from typing import Optional

from app.core.config import settings
from app.services.tiered_router.api_registry import API_REGISTRY, get_api_config
from app.services.tiered_router.circuit_breaker import CircuitBreaker, get_circuit_breaker
from app.services.tiered_router.api_logger import log_api_usage

logger = logging.getLogger(__name__)


class ParallelFetcher:
    """Fetch from multiple APIs concurrently with circuit breaker protection.

    Args:
        circuit_breaker: CircuitBreaker instance (uses singleton if not provided)
    """

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()

    async def fetch_tier(
        self,
        apis: list[str],
        query: str,
        state: dict,
    ) -> dict[str, dict]:
        """Fetch from all APIs in a tier concurrently.

        Args:
            apis: List of API names to fetch from
            query: Search query
            state: GraphState with user_id, session_id, etc.

        Returns:
            Dict mapping API name to result dict:
            {
                "api_name": {
                    "status": "success" | "timeout" | "error" | "circuit_open",
                    "api": "api_name",
                    "data": {...},  # If success
                    "error": "...",  # If error
                }
            }
        """
        active_apis = [api for api in apis if not self.circuit_breaker.is_open(api)]
        skipped_apis = [api for api in apis if self.circuit_breaker.is_open(api)]

        # Run all fetches in parallel
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

    async def _fetch_single(
        self,
        api_name: str,
        query: str,
        state: dict,
    ) -> dict:
        """Fetch from a single API with timeout and error handling.

        Args:
            api_name: Name of the API to fetch from
            query: Search query
            state: GraphState with user_id, session_id, etc.

        Returns:
            Result dict with status, api, and data or error
        """
        config = get_api_config(api_name)
        if not config:
            return {"status": "error", "api": api_name, "error": "Unknown API"}

        start_time = time.time()

        try:
            # Execute the MCP tool
            result = await asyncio.wait_for(
                self._execute_mcp_tool(
                    tool_name=config.mcp_tool,
                    provider=config.provider,
                    query=query,
                    state=state,
                ),
                timeout=config.timeout_ms / 1000,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_success(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=config.cost_cents,
                latency_ms=latency_ms,
                success=True,
            )

            return {"status": "success", "api": api_name, "data": result}

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=0,
                latency_ms=latency_ms,
                success=False,
                error="timeout",
            )

            logger.warning(f"API timeout: {api_name} after {latency_ms}ms")
            return {"status": "timeout", "api": api_name}

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

            logger.error(f"API error: {api_name} - {e}")
            return {"status": "error", "api": api_name, "error": str(e)}

    async def _execute_mcp_tool(
        self,
        tool_name: str,
        provider: str,
        query: str,
        state: dict,
    ) -> dict:
        """Execute an MCP tool and return results.

        This bridges the tiered router to existing MCP tools.

        Args:
            tool_name: MCP tool to execute
            provider: Provider key (amazon, walmart, etc.)
            query: Search query
            state: GraphState

        Returns:
            Tool result dict
        """
        # Import here to avoid circular imports
        from mcp_server.tools import tool_contracts

        # Build tool state with provider context
        tool_state = {
            **state,
            "provider": provider,
            "user_message": query,
            "search_query": query,
        }

        # Get the tool function
        tool_func = tool_contracts.get_tool_function(tool_name)
        if not tool_func:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        # Execute and extract relevant data
        result = await tool_func(tool_state)

        # Normalize result to expected format
        return {
            "products": result.get("products", result.get("search_results", [])),
            "hotels": result.get("hotels", []),
            "flights": result.get("flights", []),
            "snippets": result.get("snippets", result.get("evidence_citations", [])),
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_parallel_fetcher.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/tiered_router/parallel_fetcher.py backend/tests/test_tiered_router/test_parallel_fetcher.py
git commit -m "feat(tiered-router): add parallel fetcher with timeout and circuit breaker"
```

---

## Task 10: Orchestrator Module

**Files:**
- Create: `backend/app/services/tiered_router/orchestrator.py`
- Test: `backend/tests/test_tiered_router/test_orchestrator.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tiered_router.orchestrator import TieredAPIOrchestrator


@pytest.fixture
def orchestrator():
    return TieredAPIOrchestrator()


@pytest.fixture
def mock_state():
    return {
        "user_id": "test-user",
        "session_id": "test-session",
        "user_message": "best vacuum cleaner",
        "requested_products": [],
        "user_extended_search_enabled": False,
        "extended_search_confirmed": False,
    }


@pytest.mark.asyncio
async def test_execute_returns_success_when_sufficient(orchestrator, mock_state):
    """Should return success when Tier 1 results meet threshold"""
    with patch.object(orchestrator.fetcher, "fetch_tier", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {
            "amazon": {"status": "success", "data": {"products": [
                {"name": "p1"}, {"name": "p2"}, {"name": "p3"}
            ]}},
        }

        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "success"
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_execute_escalates_when_insufficient(orchestrator, mock_state):
    """Should escalate to Tier 2 when Tier 1 is insufficient"""
    call_count = 0

    async def mock_fetch(apis, query, state):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Tier 1 - insufficient
            return {"amazon": {"status": "success", "data": {"products": [{"name": "p1"}]}}}
        else:
            # Tier 2 - add more products
            return {"bing": {"status": "success", "data": {"products": [
                {"name": "p2"}, {"name": "p3"}, {"name": "p4"}
            ]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=mock_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "success"
    assert call_count == 2  # Called for Tier 1 and Tier 2


@pytest.mark.asyncio
async def test_execute_requires_consent_for_tier_3(orchestrator, mock_state):
    """Should return consent_required when Tier 3 is needed"""
    async def insufficient_fetch(apis, query, state):
        return {"api": {"status": "success", "data": {"products": [{"name": "p1"}]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=insufficient_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "consent_required"
    assert result["consent_prompt"]["type"] == "account_toggle"


@pytest.mark.asyncio
async def test_execute_with_consent_proceeds_to_tier_3(orchestrator):
    """Should proceed to Tier 3 when consent is given"""
    mock_state = {
        "user_id": "test-user",
        "session_id": "test-session",
        "requested_products": [],
        "user_extended_search_enabled": True,
        "extended_search_confirmed": True,
    }

    tier_calls = []

    async def track_fetch(apis, query, state):
        tier_calls.append(apis)
        if "reddit_api" in apis:
            return {"reddit_api": {"status": "success", "data": {"products": [
                {"name": "p1"}, {"name": "p2"}, {"name": "p3"}
            ]}}}
        return {"api": {"status": "success", "data": {"products": [{"name": "x"}]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=track_fetch):
        with patch("app.services.tiered_router.orchestrator.log_consent_event", new_callable=AsyncMock):
            result = await orchestrator.execute("product", "best vacuum", mock_state)

    # Should have called Tier 1, 2, and 3
    assert any("reddit_api" in apis for apis in tier_calls)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_deduplicates_items(orchestrator, mock_state):
    """Should deduplicate items across tiers"""
    async def mock_fetch(apis, query, state):
        return {
            "amazon": {"status": "success", "data": {"products": [
                {"name": "Dyson V15", "price": 599},
                {"name": "Shark Navigator", "price": 299},
            ]}},
            "walmart": {"status": "success", "data": {"products": [
                {"name": "Dyson V15", "price": 599},  # Duplicate
                {"name": "Bissell Pet", "price": 199},
            ]}},
        }

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=mock_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    # Should have 3 unique items, not 4
    assert len(result["items"]) == 3
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_orchestrator.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/tiered_router/orchestrator.py
"""Tiered API Orchestrator - Coordinates the full tier execution flow."""

import logging
from typing import Optional

from app.core.config import settings
from app.services.tiered_router.router import get_apis_for_tier, TIER_ROUTING_TABLE
from app.services.tiered_router.circuit_breaker import CircuitBreaker, get_circuit_breaker
from app.services.tiered_router.parallel_fetcher import ParallelFetcher
from app.services.tiered_router.data_validator import DataValidator, ValidationResult
from app.services.tiered_router.api_registry import API_REGISTRY
from app.services.tiered_router.api_logger import log_consent_event

logger = logging.getLogger(__name__)


class TieredAPIOrchestrator:
    """Coordinates tiered API routing flow.

    Flow:
    1. Get APIs for current tier
    2. Fetch in parallel
    3. Validate results
    4. Escalate or return
    """

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()
        self.fetcher = ParallelFetcher(self.circuit_breaker)
        self.validator = DataValidator(max_auto_tier=settings.MAX_AUTO_TIER)

    async def execute(
        self,
        intent: str,
        query: str,
        state: dict,
    ) -> dict:
        """Execute tiered API routing.

        Args:
            intent: Classified intent (product, comparison, etc.)
            query: User's search query
            state: GraphState with user context

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

        # Update state with current tier for logging
        state = {**state, "current_tier": current_tier}

        while current_tier <= 4:
            # Get APIs for this tier
            try:
                apis = get_apis_for_tier(intent, current_tier, self.circuit_breaker)
            except Exception as e:
                logger.error(f"Failed to get APIs for tier {current_tier}: {e}")
                apis = []

            if not apis:
                current_tier += 1
                state = {**state, "current_tier": current_tier}
                continue

            # Filter by feature flags
            apis = self._filter_by_feature_flags(apis)

            if not apis:
                current_tier += 1
                state = {**state, "current_tier": current_tier}
                continue

            # Fetch in parallel
            tier_results = await self.fetcher.fetch_tier(apis, query, state)
            all_results.update(tier_results)

            # Validate cumulative results
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
                        user_id=state.get("user_id", "anonymous"),
                        session_id=state.get("session_id", "unknown"),
                        consent_type="per_query",
                        tier_requested=next_tier,
                    )

                current_tier = next_tier
                state = {**state, "current_tier": current_tier}
                continue

            if validation_result == ValidationResult.CONSENT_REQUIRED:
                return self._build_consent_response(all_results, metadata, current_tier)

            if validation_result == ValidationResult.MAX_TIER_REACHED:
                return self._build_partial_response(all_results, metadata, current_tier)

        # Defensive fallback
        return self._build_partial_response(all_results, {}, current_tier)

    def _filter_by_feature_flags(self, apis: list[str]) -> list[str]:
        """Filter out APIs whose feature flags are disabled."""
        filtered = []
        for api in apis:
            config = API_REGISTRY.get(api)
            if config and config.feature_flag:
                if not getattr(settings, config.feature_flag, False):
                    continue
            filtered.append(api)
        return filtered

    def _build_success_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response for successful tier completion."""
        items, snippets = self._extract_all_data(results)
        return {
            "status": "success",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get("sources_used", []),
            "sources_unavailable": metadata.get("sources_unavailable", []),
            "tier_reached": tier,
        }

    def _build_consent_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response when consent is required."""
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

    def _build_partial_response(
        self,
        results: dict,
        metadata: dict,
        tier: int,
    ) -> dict:
        """Build response when all tiers are exhausted."""
        items, snippets = self._extract_all_data(results)
        return {
            "status": "partial",
            "items": items,
            "snippets": snippets,
            "sources_used": metadata.get(
                "sources_used",
                [k for k, v in results.items() if v.get("status") == "success"]
            ),
            "message": metadata.get("message", "Showing results from available sources"),
            "tier_reached": tier,
        }

    def _extract_all_data(self, results: dict) -> tuple[list, list]:
        """Extract and deduplicate items and snippets from results."""
        items = []
        snippets = []
        seen_items = set()

        for api_result in results.values():
            if api_result.get("status") != "success":
                continue
            data = api_result.get("data", {})

            # Extract items with deduplication
            for item in (
                data.get("products", []) +
                data.get("hotels", []) +
                data.get("flights", [])
            ):
                item_key = self._get_item_key(item)
                if item_key not in seen_items:
                    seen_items.add(item_key)
                    items.append(item)

            # Snippets (no deduplication needed)
            snippets.extend(data.get("snippets", []))

        return items, snippets

    def _get_item_key(self, item: dict) -> tuple:
        """Generate a unique key for an item for deduplication."""
        return (
            item.get("name", "").lower().strip(),
            item.get("price"),
        )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_orchestrator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/tiered_router/orchestrator.py backend/tests/test_tiered_router/test_orchestrator.py
git commit -m "feat(tiered-router): add orchestrator to coordinate tier execution"
```

---

## Task 11: LangGraph Routing Gate Node

**Files:**
- Create: `backend/app/services/langgraph/nodes/routing_gate.py`
- Test: `backend/tests/test_tiered_router/test_routing_gate.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_routing_gate.py
import pytest
from app.services.langgraph.nodes.routing_gate import routing_gate_node, DETERMINISTIC_INTENTS


@pytest.mark.asyncio
async def test_product_intent_routes_to_tiered():
    """Product intent should route to tiered executor"""
    state = {"intent": "product", "user_message": "best vacuum"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_comparison_intent_routes_to_tiered():
    """Comparison intent should route to tiered executor"""
    state = {"intent": "comparison", "user_message": "dyson vs shark"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_general_intent_routes_to_llm():
    """General intent should route to LLM planner"""
    state = {"intent": "general", "user_message": "what is a vacuum"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


@pytest.mark.asyncio
async def test_unclear_intent_routes_to_llm():
    """Unclear intent should route to LLM planner"""
    state = {"intent": "unclear", "user_message": "hmm"}

    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"


def test_deterministic_intents_contains_expected():
    """DETERMINISTIC_INTENTS should contain all expected intents"""
    expected = {"product", "comparison", "price_check", "travel", "review_deep_dive"}
    assert DETERMINISTIC_INTENTS == expected
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_routing_gate.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/langgraph/nodes/routing_gate.py
"""Routing Gate Node - Decides between tiered routing and LLM planner."""

from typing import Dict, Any

# Intents that use deterministic tiered routing
DETERMINISTIC_INTENTS = {
    "product",
    "comparison",
    "price_check",
    "travel",
    "review_deep_dive",
}


async def routing_gate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Decide whether to use tiered routing or LLM planner.

    Routes product/travel/price/comparison intents to deterministic
    tiered routing. Routes general/unclear/intro intents to LLM planner.

    Args:
        state: GraphState with intent field set

    Returns:
        Updated state with routing_mode and next_agent
    """
    intent = state.get("intent", "unclear")

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

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_routing_gate.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/langgraph/nodes/routing_gate.py backend/tests/test_tiered_router/test_routing_gate.py
git commit -m "feat(langgraph): add routing gate node for hybrid routing"
```

---

## Task 12: LangGraph Tiered Executor Node

**Files:**
- Create: `backend/app/services/langgraph/nodes/tiered_executor.py`
- Test: `backend/tests/test_tiered_router/test_tiered_executor.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tiered_router/test_tiered_executor.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.langgraph.nodes.tiered_executor import tiered_executor_node


@pytest.fixture
def mock_state():
    return {
        "intent": "product",
        "user_message": "best vacuum cleaner",
        "user_id": "test-user",
        "session_id": "test-session",
        "user_extended_search_enabled": False,
        "extended_search_confirmed": False,
    }


@pytest.mark.asyncio
async def test_success_sets_search_results(mock_state):
    """Successful execution should set search_results field"""
    mock_result = {
        "status": "success",
        "items": [{"name": "p1"}, {"name": "p2"}, {"name": "p3"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "tier_reached": 1,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["search_results"] == mock_result["items"]
    assert result["next_agent"] == "synthesizer"
    assert result.get("status") != "halted"


@pytest.mark.asyncio
async def test_consent_required_halts_workflow(mock_state):
    """Consent required should halt workflow"""
    mock_result = {
        "status": "consent_required",
        "items": [{"name": "p1"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "consent_prompt": {"type": "per_query", "message": "Search deeper?"},
        "tier_reached": 2,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["status"] == "halted"
    assert result["halt_reason"] == "consent_required"
    assert result["consent_prompt"] == mock_result["consent_prompt"]
    assert result["partial_items"] == mock_result["items"]
    assert result["next_agent"] is None


@pytest.mark.asyncio
async def test_partial_results_proceeds_to_synthesizer(mock_state):
    """Partial results should still proceed to synthesizer"""
    mock_result = {
        "status": "partial",
        "items": [{"name": "p1"}],
        "snippets": [],
        "sources_used": ["amazon"],
        "message": "Showing partial results",
        "tier_reached": 4,
    }

    with patch("app.services.langgraph.nodes.tiered_executor.orchestrator") as mock_orch:
        mock_orch.execute = AsyncMock(return_value=mock_result)

        result = await tiered_executor_node(mock_state)

    assert result["search_results"] == mock_result["items"]
    assert result["next_agent"] == "synthesizer"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_tiered_executor.py -v`
Expected: FAIL - module not found

**Step 3: Write the implementation**

```python
# backend/app/services/langgraph/nodes/tiered_executor.py
"""Tiered Executor Node - Wraps TieredAPIOrchestrator for LangGraph."""

from typing import Dict, Any

from app.services.tiered_router.orchestrator import TieredAPIOrchestrator

# Module-level orchestrator instance
orchestrator = TieredAPIOrchestrator()


async def tiered_executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tiered API routing and handle consent flow.

    Wraps TieredAPIOrchestrator.execute() and maps results to
    GraphState fields expected by downstream nodes.

    Args:
        state: GraphState with intent, user_message, user context

    Returns:
        Updated state with:
        - On success/partial: search_results, snippets, sources_used, next_agent="synthesizer"
        - On consent_required: status="halted", halt_reason, consent_prompt, partial_items
    """
    intent = state.get("intent", "product")
    query = state.get("user_message", "")

    result = await orchestrator.execute(intent, query, state)

    if result["status"] == "consent_required":
        # Halt workflow, save state, prompt user
        return {
            **state,
            "status": "halted",
            "halt_reason": "consent_required",
            "consent_prompt": result["consent_prompt"],
            "partial_items": result["items"],
            "partial_snippets": result["snippets"],
            "tier_reached": result["tier_reached"],
            "next_agent": None,  # Wait for user
        }

    # Success or partial - proceed to synthesis
    return {
        **state,
        "tier_results": result,
        "search_results": result["items"],
        "snippets": result["snippets"],
        "sources_used": result["sources_used"],
        "sources_unavailable": result.get("sources_unavailable", []),
        "tier_reached": result["tier_reached"],
        "next_agent": "synthesizer",
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_tiered_executor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/langgraph/nodes/tiered_executor.py backend/tests/test_tiered_router/test_tiered_executor.py
git commit -m "feat(langgraph): add tiered executor node"
```

---

## Task 13: Update Workflow Graph Definition

**Files:**
- Modify: `backend/app/services/langgraph/workflow.py`
- Test: `backend/tests/test_tiered_router/test_workflow_integration.py`

**Step 1: Write the integration test**

```python
# backend/tests/test_tiered_router/test_workflow_integration.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_workflow_routes_product_to_tiered():
    """Product intent should route through tiered executor"""
    # This is an integration test that verifies the workflow graph
    # routes correctly based on intent

    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "product", "user_message": "best vacuum"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "tiered"
    assert result["next_agent"] == "tiered_executor"


@pytest.mark.asyncio
async def test_workflow_routes_general_to_planner():
    """General intent should route through LLM planner"""
    from app.services.langgraph.nodes.routing_gate import routing_gate_node

    state = {"intent": "general", "user_message": "what is machine learning"}
    result = await routing_gate_node(state)

    assert result["routing_mode"] == "llm"
    assert result["next_agent"] == "planner"
```

**Step 2: Update workflow.py**

In `backend/app/services/langgraph/workflow.py`, add the following:

1. Add imports at the top:
```python
from app.services.langgraph.nodes.routing_gate import routing_gate_node
from app.services.langgraph.nodes.tiered_executor import tiered_executor_node
```

2. In the `build_workflow()` function, add the new nodes:
```python
# Add new nodes for tiered routing
workflow.add_node("routing_gate", routing_gate_node)
workflow.add_node("tiered_executor", tiered_executor_node)
```

3. Update the edge from clarifier to use routing gate:
```python
# Change: workflow.add_edge("clarifier", "planner")
# To:
workflow.add_edge("clarifier", "routing_gate")

# Add conditional routing from gate
workflow.add_conditional_edges(
    "routing_gate",
    lambda s: s.get("next_agent"),
    {
        "tiered_executor": "tiered_executor",
        "planner": "planner",
    }
)

# Add tiered executor path
workflow.add_conditional_edges(
    "tiered_executor",
    lambda s: s.get("next_agent") if s.get("status") != "halted" else END,
    {
        "synthesizer": "synthesizer",
        None: END,
    }
)
```

**Step 3: Run integration test**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_workflow_integration.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/langgraph/workflow.py backend/tests/test_tiered_router/test_workflow_integration.py
git commit -m "feat(langgraph): integrate tiered routing into workflow graph"
```

---

## Task 14: Update Chat Endpoint for Consent Resume

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Test: `backend/tests/test_tiered_router/test_consent_resume.py`

**Step 1: Write the test**

```python
# backend/tests/test_tiered_router/test_consent_resume.py
import pytest
from app.api.v1.chat import is_consent_confirmation


class MockRequest:
    def __init__(self, message=None, action=None):
        self.message = message
        self.action = action


def test_consent_confirmation_button_click():
    """Button click action should be detected"""
    request = MockRequest(action="consent_confirm")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_yes():
    """'yes' should be detected as consent"""
    request = MockRequest(message="yes")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_search_deeper():
    """'search deeper' should be detected as consent"""
    request = MockRequest(message="search deeper")
    assert is_consent_confirmation(request) is True


def test_consent_confirmation_case_insensitive():
    """Consent detection should be case insensitive"""
    request = MockRequest(message="YES")
    assert is_consent_confirmation(request) is True

    request = MockRequest(message="Search Deeper")
    assert is_consent_confirmation(request) is True


def test_non_consent_message():
    """Regular messages should not be detected as consent"""
    request = MockRequest(message="find me a vacuum")
    assert is_consent_confirmation(request) is False


def test_consent_confirmation_empty():
    """Empty request should not be consent"""
    request = MockRequest()
    assert is_consent_confirmation(request) is False
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_consent_resume.py -v`
Expected: FAIL - function not found

**Step 3: Add consent detection to chat.py**

In `backend/app/api/v1/chat.py`, add the following function:

```python
def is_consent_confirmation(request) -> bool:
    """Detect consent confirmations vs new queries.

    Args:
        request: ChatRequest with message and optional action

    Returns:
        True if this is a consent confirmation
    """
    # Structured payload from button click
    if getattr(request, "action", None) == "consent_confirm":
        return True

    # Text-based confirmation
    if request.message:
        consent_patterns = {"yes", "search deeper", "continue", "ok", "proceed", "go ahead"}
        normalized = request.message.strip().lower()
        return normalized in consent_patterns or normalized.startswith("yes")

    return False
```

**Step 4: Update chat message handler for resume flow**

In the chat message handler, add consent resume logic:

```python
async def handle_message(request: ChatRequest, session_id: str):
    halt_state = await HaltStateManager.get(session_id)

    if halt_state and halt_state.halt_reason == "consent_required":
        if is_consent_confirmation(request):
            state = halt_state.saved_state
            state["extended_search_confirmed"] = True
            await HaltStateManager.clear(session_id)

            # Resume at tiered_executor
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

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tiered_router/test_consent_resume.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_tiered_router/test_consent_resume.py
git commit -m "feat(chat): add consent detection and resume flow for Tier 3-4"
```

---

## Task 15: Update Module Exports

**Files:**
- Modify: `backend/app/services/tiered_router/__init__.py`

**Step 1: Update exports**

```python
# backend/app/services/tiered_router/__init__.py
"""Tiered API Routing System

Provides deterministic, rule-based API routing for product, travel, price,
and comparison intents with 4-tier escalation and two-layer consent.

Usage:
    from app.services.tiered_router import TieredAPIOrchestrator

    orchestrator = TieredAPIOrchestrator()
    result = await orchestrator.execute(intent, query, state)
"""

from .orchestrator import TieredAPIOrchestrator
from .router import TIER_ROUTING_TABLE, get_apis_for_tier, UnknownIntentError
from .api_registry import APIConfig, API_REGISTRY, get_api_config
from .circuit_breaker import CircuitBreaker, get_circuit_breaker
from .parallel_fetcher import ParallelFetcher
from .data_validator import DataValidator, ValidationResult, ThresholdConfig, INTENT_THRESHOLDS
from .api_logger import log_api_usage, log_consent_event

__all__ = [
    # Main orchestrator
    "TieredAPIOrchestrator",

    # Router
    "TIER_ROUTING_TABLE",
    "get_apis_for_tier",
    "UnknownIntentError",

    # API Registry
    "APIConfig",
    "API_REGISTRY",
    "get_api_config",

    # Circuit Breaker
    "CircuitBreaker",
    "get_circuit_breaker",

    # Parallel Fetcher
    "ParallelFetcher",

    # Data Validator
    "DataValidator",
    "ValidationResult",
    "ThresholdConfig",
    "INTENT_THRESHOLDS",

    # Logging
    "log_api_usage",
    "log_consent_event",
]
```

**Step 2: Commit**

```bash
git add backend/app/services/tiered_router/__init__.py
git commit -m "feat(tiered-router): update module exports"
```

---

## Task 16: Run Full Test Suite

**Step 1: Run all tiered router tests**

Run: `cd backend && python -m pytest tests/test_tiered_router/ -v`
Expected: All tests pass

**Step 2: Run existing tests to verify no regressions**

Run: `cd backend && python -m pytest tests/ -v --ignore=tests/test_tiered_router/`
Expected: No regressions in existing tests

**Step 3: Run database migrations**

Run: `cd backend && alembic upgrade head`
Expected: Migrations apply successfully

**Step 4: Commit any fixes**

If any tests fail, fix issues and commit.

---

## Task 17: Final Integration Verification

**Step 1: Start the backend**

Run: `docker-compose up -d backend`

**Step 2: Test a product query**

```bash
curl -X POST "http://localhost:8000/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "best vacuum cleaner under $500"}'
```

Expected: Response with products from Tier 1-2 APIs

**Step 3: Verify cost logging**

```bash
docker-compose exec postgres psql -U postgres -d reviewguide_db -c \
  "SELECT api_name, tier, cost_cents, success FROM api_usage_logs ORDER BY created_at DESC LIMIT 10;"
```

Expected: API calls logged with costs

**Step 4: Commit final verification**

```bash
git add -A
git commit -m "feat(tiered-router): complete implementation with integration verification"
```

---

## Summary

This implementation plan creates the tiered API routing system in 17 tasks:

| Task | Component | Tests |
|------|-----------|-------|
| 1-2 | Database migrations | N/A |
| 3 | Feature flags | N/A |
| 4 | API Registry | ✓ |
| 5 | Router | ✓ |
| 6 | Circuit Breaker | ✓ |
| 7 | Data Validator | ✓ |
| 8 | API Logger | ✓ |
| 9 | Parallel Fetcher | ✓ |
| 10 | Orchestrator | ✓ |
| 11 | Routing Gate Node | ✓ |
| 12 | Tiered Executor Node | ✓ |
| 13 | Workflow Integration | ✓ |
| 14 | Consent Resume | ✓ |
| 15 | Module Exports | N/A |
| 16-17 | Verification | N/A |

Each task follows TDD: write failing test → implement → verify → commit.
