"""
Tests for RFC §1.6 — State Payload Control and Serialization Boundaries
backend/tests/test_state_serializer.py
"""
import json
import pytest

from app.services.state_serializer import (
    safe_serialize_state,
    check_state_size,
    StateOverflowError,
)


# ---------------------------------------------------------------------------
# safe_serialize_state
# ---------------------------------------------------------------------------

def test_safe_serialize_handles_non_serializable():
    """
    A dict containing a lambda (non-JSON-serializable callable) must serialize
    without raising and must contain the placeholder string in the output.
    """
    fn = lambda x: x  # noqa: E731
    state = {"key": "value", "bad_value": fn}

    result = safe_serialize_state(state)

    # Should not raise — result must be valid JSON
    parsed = json.loads(result)

    # The lambda should have been replaced with a placeholder
    assert "bad_value" in parsed
    placeholder = parsed["bad_value"]
    assert isinstance(placeholder, str)
    assert placeholder.startswith("<non-serializable:")
    assert "function" in placeholder


def test_safe_serialize_handles_generators():
    """
    A dict containing a generator (non-JSON-serializable) must serialize
    cleanly with a placeholder instead of raising TypeError.
    """
    def _gen():
        yield 1
        yield 2

    state = {"items": _gen()}

    result = safe_serialize_state(state)

    parsed = json.loads(result)
    assert "items" in parsed
    placeholder = parsed["items"]
    assert isinstance(placeholder, str)
    assert placeholder.startswith("<non-serializable:")


def test_safe_serialize_normal_dict_unchanged():
    """
    A purely JSON-serializable dict must produce output identical to
    json.dumps() — no data loss or transformation.
    """
    state = {
        "user_message": "hello",
        "session_id": "abc-123",
        "intent": "product",
        "slots": {"destination": "Paris", "budget": 1500},
        "flags": [True, False, None],
        "score": 0.97,
    }

    result = safe_serialize_state(state)
    expected = json.dumps(state)

    # Both must round-trip to identical Python objects
    assert json.loads(result) == json.loads(expected)


# ---------------------------------------------------------------------------
# check_state_size
# ---------------------------------------------------------------------------

def test_check_state_size_raises_on_overflow():
    """
    When a key's serialized value exceeds max_bytes, StateOverflowError
    must be raised with a descriptive message.
    """
    big_list = ["x" * 100] * 200  # ~20 KB of data
    state = {"search_results": big_list}

    # Use a tiny limit (100 bytes) to guarantee overflow
    with pytest.raises(StateOverflowError) as exc_info:
        check_state_size(state, "search_results", max_bytes=100)

    error_message = str(exc_info.value)
    assert "search_results" in error_message
    assert "exceeds the limit" in error_message


def test_check_state_size_passes_under_limit():
    """
    When a key's serialized value is within max_bytes, no exception is raised.
    """
    state = {"slots": {"destination": "Rome"}}

    # Large limit — should not raise
    check_state_size(state, "slots", max_bytes=10_240)  # 10 KB limit


def test_check_state_size_missing_key_is_noop():
    """
    If the key is not present in the state dict, check_state_size must
    silently do nothing (no KeyError, no StateOverflowError).
    """
    state = {"intent": "travel"}

    # Key does not exist — should not raise anything
    check_state_size(state, "nonexistent_key", max_bytes=100)
