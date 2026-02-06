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
