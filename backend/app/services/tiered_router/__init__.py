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
