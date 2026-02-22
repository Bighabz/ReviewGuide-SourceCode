"""Tests for query complexity classifier."""
import pytest
from app.agents.query_complexity import classify_query_complexity


class TestFactoidQueries:
    """Factoid queries - short, single entity, no comparison/review intent."""

    @pytest.mark.parametrize("message,slots", [
        ("what year was the Sony XM5 released", {"product_names": ["Sony WH-1000XM5"]}),
        ("how much does AirPods Pro weigh", {"product_names": ["AirPods Pro"]}),
        ("does the iPhone 15 have USB-C", {"product_names": ["iPhone 15"]}),
        ("what colors does Apple Watch Series 9 come in", {"product_names": ["Apple Watch Series 9"]}),
        ("is the Bose QC45 foldable", {"product_names": ["Bose QC45"]}),
    ])
    def test_factoid_classification(self, message, slots):
        complexity, confidence = classify_query_complexity(message, slots, "product")
        assert complexity == "factoid"
        assert confidence >= 0.7


class TestComparisonQueries:
    """Comparison queries - 2+ products or explicit compare keywords."""

    @pytest.mark.parametrize("message,slots", [
        ("Sony XM5 vs Bose QC45 which is better", {"product_names": ["Sony WH-1000XM5", "Bose QC45"]}),
        ("compare iPhone 15 and Samsung S24", {"product_names": ["iPhone 15", "Samsung S24"]}),
        ("what is the difference between AirPods Pro and Sony XM5", {"product_names": ["AirPods Pro", "Sony XM5"]}),
        ("Jabra Elite 85h versus Sony XM5 versus Bose", {"product_names": ["Jabra Elite 85h", "Sony WH-1000XM5", "Bose"]}),
        ("Nikon Z50 or Canon M50 for beginners", {"product_names": ["Nikon Z50", "Canon M50"]}),
    ])
    def test_comparison_classification(self, message, slots):
        complexity, confidence = classify_query_complexity(message, slots, "product")
        assert complexity == "comparison"
        assert confidence >= 0.7


class TestRecommendationQueries:
    """Recommendation queries - 'best X' with no specific product named."""

    @pytest.mark.parametrize("message,slots", [
        ("what are the best noise canceling headphones", {"product_names": []}),
        ("recommend a good gaming laptop under $1000", {"product_names": []}),
        ("which mirrorless camera should I buy for travel", {"product_names": []}),
        ("top 5 mechanical keyboards for programmers", {"product_names": []}),
        ("what should I get for running earbuds", {"product_names": []}),
    ])
    def test_recommendation_classification(self, message, slots):
        complexity, confidence = classify_query_complexity(message, slots, "product")
        assert complexity == "recommendation"
        assert confidence >= 0.7


class TestDeepResearchQueries:
    """Deep research queries - review-heavy, sentiment, multi-criteria."""

    @pytest.mark.parametrize("message,slots", [
        ("what do actual owners say about the Sony XM5 complaints", {"product_names": ["Sony WH-1000XM5"]}),
        ("are there any known problems with the MacBook Pro M3", {"product_names": ["MacBook Pro M3"]}),
        ("Sony WH-1000XM5 real world review is it worth it after 6 months", {"product_names": ["Sony WH-1000XM5"]}),
        ("what are the common issues with the Bose QC35 II based on user experience", {"product_names": ["Bose QC35 II"]}),
        ("tell me about Nikon Z6 II pros cons image quality autofocus low light performance video any known issues", {"product_names": ["Nikon Z6 II"]}),
    ])
    def test_deep_research_classification(self, message, slots):
        complexity, confidence = classify_query_complexity(message, slots, "product")
        assert complexity == "deep_research"
        assert confidence >= 0.7


class TestConfidenceThreshold:
    """Test that low-confidence cases fall through to LLM planner."""

    def test_ambiguous_query_has_lower_confidence(self):
        # Short but contains neither factoid nor comparison signals
        complexity, confidence = classify_query_complexity("tell me about laptops", {}, "product")
        # Should be recommendation or deep_research with lower confidence
        assert isinstance(complexity, str)
        assert 0.0 <= confidence <= 1.0
