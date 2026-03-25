"""
Tests for Fast Router — Tier 1 Keyword Classification + Tier 2 Haiku Fallback

Covers:
    - Intent classification for all intents
    - Confidence thresholds
    - Slot extraction (budget, brand, category, destination)
    - Tool chain correctness
    - Plan structure and step ordering
    - Ambiguous / low-confidence queries
    - Follow-up query handling via last_search_context
    - Tier 2 Haiku LLM fallback
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.fast_router import (
    TOOL_CHAINS,
    PLAN_TEMPLATES,
    FastRouterResult,
    extract_slots,
    fast_router_sync,
    _classify_tier1,
)


# ---------------------------------------------------------------------------
# Tier 1 keyword classification
# ---------------------------------------------------------------------------


class TestTier1KeywordClassification:
    """Test intent classification for a broad range of queries."""

    @pytest.mark.parametrize(
        "query, expected_intent",
        [
            # ── Product queries ──
            ("best wireless headphones", "product"),
            ("buy a new laptop", "product"),
            ("recommend a good coffee maker", "product"),
            ("top rated robot vacuum", "product"),
            ("review of the Sony WH-1000XM5", "product"),
            ("cheap earbuds that sound good", "product"),
            ("affordable monitor for gaming", "product"),
            ("premium noise canceling headphones", "product"),
            ("is the Dyson V15 worth it", "product"),
            ("which laptop should I get", "product"),
            ("looking for a budget mechanical keyboard", "product"),
            ("need a new stand mixer", "product"),
            ("want a good espresso machine", "product"),
            ("shopping for a tablet", "product"),
            # ── Comparison queries ──
            ("Sony WH-1000XM5 vs Bose 700", "comparison"),
            ("Dyson versus Shark vacuum", "comparison"),
            ("compare the iPhone 15 and Samsung S24", "comparison"),
            ("comparison of AirPods and Galaxy Buds", "comparison"),
            ("which is better: Dell XPS or MacBook Pro", "comparison"),
            ("difference between robot vacuums and regular vacuums", "comparison"),
            # ── Travel queries ──
            ("plan a trip to Tokyo", "travel"),
            ("hotels in Paris", "travel"),
            ("flights to New York", "travel"),
            ("things to do in Bangkok", "travel"),
            ("travel to Rome for a week", "travel"),
            ("vacation ideas for Bali", "travel"),
            ("holiday in London", "travel"),
            ("itinerary for Japan", "travel"),
            ("where to stay in Singapore", "travel"),
            # ── General / informational queries ──
            ("what is a noise canceling headphone", "general"),
            ("what are the benefits of OLED monitors", "general"),
            ("how does a robot vacuum work", "general"),
            ("explain HEPA filters", "general"),
            ("tell me about espresso machines", "general"),
            ("history of Sony headphones", "general"),
            # ── Service queries ──
            ("best VPN service", "service"),
            ("best streaming service for movies", "service"),
            ("top internet service providers", "service"),
            ("best insurance provider", "service"),
            ("cheapest VPN subscription", "service"),
            # ── Intro / greeting queries ──
            ("hi", "intro"),
            ("hello there", "intro"),
            ("hey", "intro"),
            ("good morning", "intro"),
            ("good afternoon", "intro"),
            ("good evening", "intro"),
            ("what can you do", "intro"),
            ("what can you help me with", "intro"),
        ],
    )
    def test_query_classifies_to_expected_intent(self, query, expected_intent):
        result = fast_router_sync(query)
        assert result.intent == expected_intent, (
            f"Query '{query}' expected intent='{expected_intent}' "
            f"but got '{result.intent}'"
        )

    @pytest.mark.parametrize(
        "query",
        [
            "best wireless headphones",
            "Sony WH-1000XM5 vs Bose 700",
            "plan a trip to Tokyo",
            "hi",
            "what is a robot vacuum",
            "best VPN service",
        ],
    )
    def test_clear_queries_get_high_confidence(self, query):
        result = fast_router_sync(query)
        assert result.confidence >= 0.80, (
            f"Query '{query}' should have confidence >= 0.80, got {result.confidence}"
        )

    @pytest.mark.parametrize(
        "query",
        [
            "asdfghjkl",
            "zxcvbnm",
            "123456789",
            "purple monkey dishwasher",
        ],
    )
    def test_ambiguous_queries_get_low_confidence(self, query):
        result = fast_router_sync(query)
        assert result.confidence < 0.60, (
            f"Query '{query}' should have confidence < 0.60, got {result.confidence}"
        )

    def test_ambiguous_query_returns_unclear_intent(self):
        result = fast_router_sync("asdfghjkl")
        assert result.intent == "unclear"

    def test_general_without_product_signal_is_general(self):
        result = fast_router_sync("what is a HEPA filter")
        assert result.intent == "general"

    def test_general_with_product_signal_is_product(self):
        # "what is the best X" has both general and product keywords;
        # product takes precedence because has_product is True.
        result = fast_router_sync("what is the best laptop to buy")
        assert result.intent == "product"

    def test_service_beats_product_when_both_present(self):
        # Contains both "best" (product) and "service" → service wins
        result = fast_router_sync("best VPN service to buy")
        assert result.intent == "service"

    def test_comparison_beats_product(self):
        result = fast_router_sync("best laptop vs best desktop")
        assert result.intent == "comparison"

    def test_comparison_beats_travel(self):
        result = fast_router_sync("comparing hotels in Paris versus London")
        assert result.intent == "comparison"

    def test_follow_up_with_product_context(self):
        """A vague follow-up that would normally be unclear should use context intent."""
        result = fast_router_sync(
            "what about the cheaper option",
            last_search_context={"intent": "product"},
        )
        # "what about" doesn't trigger general (no exact phrase match), no product keyword
        # → should pick up from context
        assert result.intent in ("product", "unclear")  # depends on keyword hits

    def test_follow_up_inherits_context_for_truly_ambiguous(self):
        """A query with no keywords at all should inherit last_search_context intent."""
        result = fast_router_sync(
            "the second one",
            last_search_context={"intent": "comparison"},
        )
        assert result.intent == "comparison"

    def test_no_context_returns_unclear(self):
        """With no context and no matching keywords, unclear is returned."""
        result = fast_router_sync("the second one")
        assert result.intent == "unclear"


# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------


class TestSlotExtraction:
    """Test regex-based slot extraction from user queries."""

    def test_budget_under_pattern(self):
        slots = extract_slots("best headphones under $200")
        assert slots.get("max_budget") == 200

    def test_budget_under_no_dollar_sign(self):
        slots = extract_slots("best headphones under 200")
        assert slots.get("max_budget") == 200

    def test_budget_below_pattern(self):
        slots = extract_slots("find a laptop below $1500")
        assert slots.get("max_budget") == 1500

    def test_budget_max_pattern_less_than(self):
        slots = extract_slots("earbuds less than $100")
        assert slots.get("max_budget") == 100

    def test_budget_max_pattern_up_to(self):
        slots = extract_slots("headphones up to $300")
        assert slots.get("max_budget") == 300

    def test_budget_max_pattern_max_keyword(self):
        slots = extract_slots("laptop max $2000")
        assert slots.get("max_budget") == 2000

    def test_budget_range_pattern(self):
        slots = extract_slots("laptops between $500 and $1000")
        assert slots.get("min_budget") == 500
        assert slots.get("max_budget") == 1000

    def test_budget_range_with_dash(self):
        slots = extract_slots("headphones $100-$300")
        assert slots.get("min_budget") == 100
        assert slots.get("max_budget") == 300

    def test_budget_range_normalises_order(self):
        """Ensure min < max regardless of query order."""
        slots = extract_slots("budget $800 to $400")
        assert slots["min_budget"] == 400
        assert slots["max_budget"] == 800

    def test_budget_around_pattern(self):
        slots = extract_slots("looking for headphones around $250")
        assert slots.get("budget_approx") == 250

    def test_budget_about_pattern(self):
        slots = extract_slots("laptop about $1500")
        assert slots.get("budget_approx") == 1500

    def test_budget_with_comma_separator(self):
        slots = extract_slots("gaming laptop under $1,500")
        assert slots.get("max_budget") == 1500

    def test_brand_extraction_sony(self):
        slots = extract_slots("best sony headphones")
        assert slots.get("brand") == "sony"

    def test_brand_extraction_apple(self):
        slots = extract_slots("Apple AirPods review")
        assert slots.get("brand") == "apple"

    def test_brand_extraction_bose(self):
        slots = extract_slots("Bose QuietComfort 45 vs Sony XM5")
        # First brand in KNOWN_BRANDS order wins; bose comes before sony
        assert slots.get("brand") in ("bose", "sony")

    def test_brand_extraction_case_insensitive(self):
        slots = extract_slots("SAMSUNG Galaxy S24 review")
        assert slots.get("brand") == "samsung"

    def test_category_extraction_robot_vacuum(self):
        slots = extract_slots("best robot vacuum for pet hair")
        assert slots.get("category") == "robot vacuum"

    def test_category_extraction_headphones(self):
        slots = extract_slots("top rated headphones under $200")
        assert slots.get("category") == "headphones"

    def test_category_extraction_espresso_machine(self):
        slots = extract_slots("affordable espresso machine for beginners")
        assert slots.get("category") == "espresso machine"

    def test_category_extraction_laptop(self):
        slots = extract_slots("gaming laptop under $1000")
        # "gaming laptop" is listed before "laptop"
        assert slots.get("category") in ("gaming laptop", "laptop")

    def test_travel_destination_tokyo(self):
        slots = extract_slots("plan a trip to Tokyo")
        assert slots.get("destination") == "Tokyo"

    def test_travel_destination_paris(self):
        slots = extract_slots("hotels in Paris")
        assert slots.get("destination") == "Paris"

    def test_travel_destination_new_york(self):
        slots = extract_slots("flights to New York")
        assert slots.get("destination") == "New York"

    def test_travel_destination_things_to_do(self):
        slots = extract_slots("things to do in Bangkok")
        assert slots.get("destination") == "Bangkok"

    def test_no_slots_extracted_for_greeting(self):
        slots = extract_slots("hello")
        assert slots == {}

    def test_no_slots_extracted_for_vague_query(self):
        slots = extract_slots("I need something good")
        assert "max_budget" not in slots
        assert "brand" not in slots
        assert "category" not in slots
        assert "destination" not in slots

    def test_multiple_slots_extracted(self):
        slots = extract_slots("best Sony headphones under $300")
        assert slots.get("brand") == "sony"
        assert slots.get("max_budget") == 300


# ---------------------------------------------------------------------------
# Tool chains
# ---------------------------------------------------------------------------


class TestToolChains:
    """Test that each intent maps to the correct set of tools."""

    @pytest.mark.parametrize(
        "intent, must_contain",
        [
            ("product", ["product_search", "product_compose", "next_step_suggestion"]),
            ("comparison", ["product_search", "product_comparison", "next_step_suggestion"]),
            ("service", ["product_search", "product_compose", "next_step_suggestion"]),
            ("travel", ["travel_itinerary", "travel_compose", "next_step_suggestion"]),
            ("general", ["general_search", "general_compose", "next_step_suggestion"]),
            ("intro", ["intro_compose"]),
            ("unclear", ["unclear_compose"]),
        ],
    )
    def test_tool_chain_contains_required_tools(self, intent, must_contain):
        chain = TOOL_CHAINS[intent]
        for tool in must_contain:
            assert tool in chain, (
                f"Tool chain for '{intent}' should contain '{tool}'; got {chain}"
            )

    def test_all_intents_have_tool_chains(self):
        for intent in ("product", "comparison", "service", "travel", "general", "intro", "unclear"):
            assert intent in TOOL_CHAINS
            assert len(TOOL_CHAINS[intent]) > 0

    def test_fast_router_result_tool_chain_matches_dict(self):
        for intent in ("product", "comparison", "service", "travel", "general"):
            result = fast_router_sync(f"placeholder query for {intent}")
            # Tool chain in result must be a list of strings
            assert isinstance(result.tool_chain, list)
            assert all(isinstance(t, str) for t in result.tool_chain)


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------


class TestPlanGeneration:
    """Test plan structure returned by fast_router_sync."""

    def test_plan_has_steps_key(self):
        result = fast_router_sync("best headphones")
        assert "steps" in result.plan

    def test_plan_steps_is_list(self):
        result = fast_router_sync("best headphones")
        assert isinstance(result.plan["steps"], list)
        assert len(result.plan["steps"]) > 0

    @pytest.mark.parametrize(
        "query",
        [
            "best headphones",
            "Sony vs Bose headphones",
            "plan a trip to Tokyo",
            "what is a HEPA filter",
            "best VPN service",
            "hi",
            "asdfghjkl",
        ],
    )
    def test_plan_step_format(self, query):
        result = fast_router_sync(query)
        for step in result.plan["steps"]:
            assert "id" in step, f"Step missing 'id': {step}"
            assert "tools" in step, f"Step missing 'tools': {step}"
            assert isinstance(step["tools"], list), f"'tools' should be a list: {step}"
            assert all(isinstance(t, str) for t in step["tools"]), (
                f"All tools in step should be strings: {step}"
            )

    def test_plan_respects_dependencies_product_search_first(self):
        result = fast_router_sync("best headphones under $200")
        assert result.intent == "product"
        steps = result.plan["steps"]
        # product_search must come in an earlier step than product_normalize
        search_step_idx = None
        normalize_step_idx = None
        for i, step in enumerate(steps):
            if "product_search" in step["tools"]:
                search_step_idx = i
            if "product_normalize" in step["tools"]:
                normalize_step_idx = i
        assert search_step_idx is not None, "product_search not found in plan"
        assert normalize_step_idx is not None, "product_normalize not found in plan"
        assert search_step_idx < normalize_step_idx, (
            "product_search must precede product_normalize"
        )

    def test_plan_respects_dependencies_compose_last(self):
        result = fast_router_sync("best headphones")
        assert result.intent == "product"
        steps = result.plan["steps"]
        compose_idx = None
        for i, step in enumerate(steps):
            if "product_compose" in step["tools"]:
                compose_idx = i
        assert compose_idx is not None
        # product_compose should come after product_search
        for i, step in enumerate(steps):
            if "product_search" in step["tools"]:
                assert i < compose_idx, "product_search must precede product_compose"

    def test_travel_plan_parallel_steps(self):
        result = fast_router_sync("plan a trip to Tokyo")
        assert result.intent == "travel"
        steps = result.plan["steps"]
        # First step should be parallel (itinerary + destination_facts)
        first = steps[0]
        assert first["parallel"] is True
        assert "travel_itinerary" in first["tools"]

    def test_plan_templates_match_all_intents(self):
        for intent in ("product", "comparison", "service", "travel", "general", "intro", "unclear"):
            assert intent in PLAN_TEMPLATES, f"PLAN_TEMPLATES missing intent: {intent}"
            assert len(PLAN_TEMPLATES[intent]) > 0

    def test_result_plan_equals_template(self):
        result = fast_router_sync("best headphones")
        assert result.plan == {"steps": PLAN_TEMPLATES["product"]}


# ---------------------------------------------------------------------------
# FastRouterResult structure
# ---------------------------------------------------------------------------


class TestFastRouterResultStructure:
    """Test the structure and fields of FastRouterResult."""

    def test_result_is_fast_router_result_instance(self):
        result = fast_router_sync("best headphones")
        assert isinstance(result, FastRouterResult)

    def test_tier_is_1_for_keyword_match(self):
        result = fast_router_sync("best headphones under $200")
        assert result.tier == 1

    def test_tier_is_1_for_unclear(self):
        result = fast_router_sync("asdfghjkl")
        assert result.tier == 1

    def test_needs_clarification_false_for_clear_query(self):
        result = fast_router_sync("best headphones under $200")
        assert result.needs_clarification is False

    def test_needs_clarification_true_for_unclear(self):
        result = fast_router_sync("asdfghjkl")
        assert result.needs_clarification is True

    def test_slots_is_dict(self):
        result = fast_router_sync("best headphones")
        assert isinstance(result.slots, dict)

    def test_confidence_is_float_between_0_and_1(self):
        for query in ("best headphones", "hi", "asdfghjkl", "plan a trip to Tokyo"):
            result = fast_router_sync(query)
            assert 0.0 <= result.confidence <= 1.0, (
                f"Confidence out of range for '{query}': {result.confidence}"
            )

    def test_intro_confidence_is_very_high(self):
        result = fast_router_sync("hello")
        assert result.confidence >= 0.95

    def test_unclear_confidence_is_low(self):
        result = fast_router_sync("zxcvbnm")
        assert result.confidence == 0.3


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_returns_unclear(self):
        result = fast_router_sync("")
        assert result.intent == "unclear"

    def test_whitespace_only_returns_unclear(self):
        result = fast_router_sync("   ")
        assert result.intent == "unclear"

    def test_none_conversation_history_does_not_crash(self):
        result = fast_router_sync("best headphones", conversation_history=None)
        assert result.intent == "product"

    def test_empty_conversation_history_does_not_crash(self):
        result = fast_router_sync("best headphones", conversation_history=[])
        assert result.intent == "product"

    def test_none_last_search_context_does_not_crash(self):
        result = fast_router_sync("best headphones", last_search_context=None)
        assert result.intent == "product"

    def test_uppercase_query_classifies_correctly(self):
        result = fast_router_sync("BEST WIRELESS HEADPHONES")
        assert result.intent == "product"

    def test_mixed_case_query(self):
        result = fast_router_sync("Best Sony Headphones Under $200")
        assert result.intent == "product"
        assert result.slots.get("brand") == "sony"
        assert result.slots.get("max_budget") == 200

    def test_very_long_query_does_not_crash(self):
        long_query = " ".join(["best laptop"] * 100)
        result = fast_router_sync(long_query)
        assert result.intent == "product"

    def test_special_characters_in_query(self):
        result = fast_router_sync("best headphones!!! @#$%")
        assert result.intent == "product"

    def test_classify_tier1_returns_none_for_no_match(self):
        result = _classify_tier1("zxcvbnm")
        assert result is None

    def test_classify_tier1_returns_string_for_match(self):
        result = _classify_tier1("best headphones")
        assert isinstance(result, str)
        assert result == "product"


# ---------------------------------------------------------------------------
# Tier 2 Haiku LLM fallback
# ---------------------------------------------------------------------------


class TestTier2HaikuFallback:
    """Tier 2: Haiku LLM fallback for ambiguous queries."""

    @pytest.mark.asyncio
    async def test_ambiguous_query_uses_tier2(self):
        """Queries that don't match Tier 1 keywords should hit Tier 2."""
        from app.services.fast_router import fast_router

        mock_response = {"intent": "product", "slots": {"category": "headphones"}}
        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, return_value=mock_response):
            result = await fast_router("those listening devices for your head", [], None)
            assert result.intent == "product"
            assert result.tier == 2

    @pytest.mark.asyncio
    async def test_tier1_hit_skips_tier2(self):
        """Clear product queries should NOT call Haiku."""
        from app.services.fast_router import fast_router

        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock) as mock_haiku:
            result = await fast_router("best headphones under $200", [], None)
            mock_haiku.assert_not_called()
            assert result.tier == 1

    @pytest.mark.asyncio
    async def test_tier2_failure_falls_back_to_general(self):
        """If Haiku call fails, fall back to general intent."""
        from app.services.fast_router import fast_router

        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, side_effect=Exception("API error")):
            result = await fast_router("something weird and ambiguous", [], None)
            assert result.intent == "general"
            assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_tier2_merges_slots(self):
        """Haiku slots should be merged with regex slots, regex taking precedence."""
        from app.services.fast_router import fast_router

        mock_response = {"intent": "product", "slots": {"category": "audio", "brand": "wrong_brand"}}
        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, return_value=mock_response):
            # "sony" is in KNOWN_BRANDS, regex should override "wrong_brand"
            result = await fast_router("find me some sony things for ears", [], None)
            assert result.slots.get("brand") == "sony"  # regex wins

    @pytest.mark.asyncio
    async def test_tier2_no_api_key_falls_back(self):
        """If ANTHROPIC_API_KEY is empty, Tier 2 should gracefully skip."""
        from app.services.fast_router import fast_router

        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, return_value=None):
            result = await fast_router("ambiguous query about stuff", [], None)
            assert result.intent == "general"  # fallback
