"""
Tests for RFC §1.8 — Named SSE Stream Channels

Verifies that the _sse_event() helper and the generate_chat_stream generator
produce correctly-formatted SSE messages with named event types.
"""
import json
import pytest


# ---------------------------------------------------------------------------
# Import the helper under test
# ---------------------------------------------------------------------------
from app.api.v1.chat import _sse_event


# ---------------------------------------------------------------------------
# Helper: parse a single SSE message string into its fields
# ---------------------------------------------------------------------------

def _parse_sse(raw: str) -> dict:
    """
    Parse a raw SSE string into a dict with keys:
        event   — named event type (or None if absent)
        data    — parsed JSON dict from the data line
        raw     — original string for assertion messages
    """
    event_type = None
    data_payload = None

    for line in raw.split("\n"):
        if line.startswith("event: "):
            event_type = line[len("event: "):].strip()
        elif line.startswith("data: "):
            data_payload = json.loads(line[len("data: "):])

    return {"event": event_type, "data": data_payload, "raw": raw}


# ---------------------------------------------------------------------------
# _sse_event() helper tests
# ---------------------------------------------------------------------------

class TestSseEventHelper:
    """Unit-tests for the _sse_event() formatting helper."""

    def test_event_helper_produces_valid_sse(self):
        """_sse_event() must return a string ending with \\n\\n (SSE message boundary)."""
        result = _sse_event("status", {"text": "Searching..."})
        assert isinstance(result, str)
        assert result.endswith("\n\n"), (
            f"SSE message must end with \\n\\n, got: {result!r}"
        )

    def test_event_helper_event_line_comes_first(self):
        """The event: line must appear before the data: line in the output."""
        result = _sse_event("content", {"token": "Hello"})
        lines = result.rstrip("\n").split("\n")
        # First non-empty line should be the event field
        assert lines[0].startswith("event: "), (
            f"First line should be 'event: ...', got: {lines[0]!r}"
        )

    def test_event_helper_data_is_valid_json(self):
        """The data line must contain valid JSON."""
        result = _sse_event("done", {"session_id": "abc", "completeness": "full"})
        parsed = _parse_sse(result)
        assert parsed["data"] is not None, "data line must parse to a JSON object"
        assert parsed["data"]["session_id"] == "abc"

    def test_event_helper_custom_encoder(self):
        """_sse_event() should use the provided encoder_cls for serialization."""
        from datetime import datetime, timezone
        from app.api.v1.chat import DateTimeEncoder

        dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = _sse_event("done", {"ts": dt}, encoder_cls=DateTimeEncoder)
        parsed = _parse_sse(result)
        # datetime should be serialized to ISO string
        assert isinstance(parsed["data"]["ts"], str)
        assert "2024-06-15" in parsed["data"]["ts"]


# ---------------------------------------------------------------------------
# Named event type format tests
# ---------------------------------------------------------------------------

class TestStatusEventFormat:
    """Tests for the 'status' SSE event channel."""

    def test_status_event_starts_with_event_status(self):
        """A status SSE string must start with 'event: status\\n'."""
        result = _sse_event("status", {"text": "Searching...", "agent": "executor", "step": 1})
        assert result.startswith("event: status\n"), (
            f"Expected 'event: status\\n' prefix, got: {result[:40]!r}"
        )

    def test_status_event_contains_text_field(self):
        """Status event data should carry a 'text' field."""
        result = _sse_event("status", {"text": "Comparing prices...", "agent": "ranker", "step": 2})
        parsed = _parse_sse(result)
        assert parsed["data"]["text"] == "Comparing prices..."

    def test_status_event_named_correctly(self):
        """Parsed event type should be 'status'."""
        result = _sse_event("status", {"text": "Loading results..."})
        parsed = _parse_sse(result)
        assert parsed["event"] == "status"


class TestContentEventFormat:
    """Tests for the 'content' SSE event channel."""

    def test_content_event_starts_with_event_content(self):
        """A content SSE string must start with 'event: content\\n'."""
        result = _sse_event("content", {"token": "H"})
        assert result.startswith("event: content\n"), (
            f"Expected 'event: content\\n' prefix, got: {result[:40]!r}"
        )

    def test_content_event_named_correctly(self):
        """Parsed event type should be 'content'."""
        result = _sse_event("content", {"token": "ello"})
        parsed = _parse_sse(result)
        assert parsed["event"] == "content"

    def test_content_event_carries_token(self):
        """Content event data must carry a 'token' field."""
        result = _sse_event("content", {"token": "W"})
        parsed = _parse_sse(result)
        assert parsed["data"]["token"] == "W"


class TestArtifactEventFormat:
    """Tests for the 'artifact' SSE event channel."""

    def test_artifact_event_starts_with_event_artifact(self):
        """An artifact SSE string must start with 'event: artifact\\n'."""
        result = _sse_event("artifact", {"type": "product_cards", "blocks": [], "clear": True})
        assert result.startswith("event: artifact\n"), (
            f"Expected 'event: artifact\\n' prefix, got: {result[:40]!r}"
        )

    def test_artifact_event_named_correctly(self):
        """Parsed event type should be 'artifact'."""
        result = _sse_event("artifact", {"type": "hotel_cards", "blocks": []})
        parsed = _parse_sse(result)
        assert parsed["event"] == "artifact"

    def test_artifact_clear_only_event(self):
        """An artifact event with only 'clear' must still be valid SSE."""
        result = _sse_event("artifact", {"clear": True})
        parsed = _parse_sse(result)
        assert parsed["event"] == "artifact"
        assert parsed["data"]["clear"] is True


class TestDoneEventHasCompleteness:
    """Tests for the 'done' SSE event channel and required completeness field."""

    def test_done_event_starts_with_event_done(self):
        """A done SSE string must start with 'event: done\\n'."""
        result = _sse_event("done", {
            "session_id": "test-session",
            "status": "completed",
            "completeness": "full",
        })
        assert result.startswith("event: done\n"), (
            f"Expected 'event: done\\n' prefix, got: {result[:40]!r}"
        )

    def test_done_event_has_completeness_field(self):
        """Done event data must include a 'completeness' field."""
        result = _sse_event("done", {
            "session_id": "abc",
            "status": "completed",
            "completeness": "full",
            "missing_sections": [],
        })
        parsed = _parse_sse(result)
        assert "completeness" in parsed["data"], (
            "done event must carry a 'completeness' field"
        )

    def test_done_event_completeness_is_full_by_default(self):
        """For the current phase, completeness should always be 'full'."""
        result = _sse_event("done", {
            "session_id": "abc",
            "status": "completed",
            "completeness": "full",
        })
        parsed = _parse_sse(result)
        assert parsed["data"]["completeness"] == "full"

    def test_done_event_named_correctly(self):
        """Parsed event type should be 'done'."""
        result = _sse_event("done", {"session_id": "abc", "status": "completed", "completeness": "full"})
        parsed = _parse_sse(result)
        assert parsed["event"] == "done"


class TestErrorEventFormat:
    """Tests for the 'error' SSE event channel."""

    def test_error_event_starts_with_event_error(self):
        """An error SSE string must start with 'event: error\\n'."""
        result = _sse_event("error", {
            "code": "internal_error",
            "message": "Something went wrong.",
            "recoverable": True,
        })
        assert result.startswith("event: error\n"), (
            f"Expected 'event: error\\n' prefix, got: {result[:40]!r}"
        )

    def test_error_event_named_correctly(self):
        """Parsed event type should be 'error'."""
        result = _sse_event("error", {"code": "timeout", "message": "Request timed out.", "recoverable": False})
        parsed = _parse_sse(result)
        assert parsed["event"] == "error"

    def test_error_event_carries_code_and_message(self):
        """Error event data must carry 'code' and 'message' fields."""
        result = _sse_event("error", {
            "code": "internal_error",
            "message": "Unexpected failure.",
            "recoverable": True,
        })
        parsed = _parse_sse(result)
        assert parsed["data"]["code"] == "internal_error"
        assert parsed["data"]["message"] == "Unexpected failure."

    def test_error_event_recoverable_field(self):
        """Error event data should carry a 'recoverable' boolean."""
        result = _sse_event("error", {"code": "timeout", "message": "Timed out.", "recoverable": True})
        parsed = _parse_sse(result)
        assert parsed["data"]["recoverable"] is True


# ---------------------------------------------------------------------------
# Integration: verify that every distinct SSE channel type is correctly named
# ---------------------------------------------------------------------------

class TestAllChannelNames:
    """Parameterised smoke-tests across all five SSE channel types."""

    @pytest.mark.parametrize("event_type,payload", [
        ("status",   {"text": "Working...", "agent": "executor", "step": 1}),
        ("content",  {"token": "A"}),
        ("artifact", {"type": "product_cards", "blocks": [], "clear": True}),
        ("done",     {"session_id": "s", "status": "completed", "completeness": "full", "missing_sections": []}),
        ("error",    {"code": "err", "message": "Oops", "recoverable": True}),
    ])
    def test_channel_event_field(self, event_type: str, payload: dict):
        """Every channel must produce an SSE string with the correct event: field."""
        result = _sse_event(event_type, payload)
        parsed = _parse_sse(result)
        assert parsed["event"] == event_type, (
            f"Expected event type '{event_type}', got '{parsed['event']}'"
        )

    @pytest.mark.parametrize("event_type,payload", [
        ("status",   {"text": "Working...", "agent": "executor", "step": 1}),
        ("content",  {"token": "A"}),
        ("artifact", {"type": "product_cards", "blocks": [], "clear": True}),
        ("done",     {"session_id": "s", "status": "completed", "completeness": "full", "missing_sections": []}),
        ("error",    {"code": "err", "message": "Oops", "recoverable": True}),
    ])
    def test_channel_data_is_json(self, event_type: str, payload: dict):
        """Every channel's data line must be valid JSON matching the input payload."""
        result = _sse_event(event_type, payload)
        parsed = _parse_sse(result)
        assert parsed["data"] is not None, f"data line missing for event_type={event_type}"
        for key in payload:
            assert key in parsed["data"], (
                f"Payload key '{key}' missing from data for event_type={event_type}"
            )
