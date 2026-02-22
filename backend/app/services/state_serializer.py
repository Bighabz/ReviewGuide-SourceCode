"""
State Serializer — RFC §1.6: State Payload Control and Serialization Boundaries

Provides safe JSON serialization for GraphState with non-serializable value stripping
and size-guard infrastructure to prevent Redis payload bloat.
"""
import json
from datetime import datetime, date
from app.core.centralized_logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Size limits (bytes) — RFC §1.6
# ---------------------------------------------------------------------------
MAX_CONTROL_STATE_BYTES = 10_240    # 10 KB — intent, slots, followups, etc.
MAX_TOOL_INPUTS_BYTES = 51_200     # 50 KB — search_results, raw tool inputs
MAX_UI_PROJECTION_BYTES = 512_000  # 500 KB — ui_blocks, assistant_text, etc.


class StateOverflowError(Exception):
    """
    Raised when a GraphState key exceeds its configured size limit.

    Callers that do not want to crash on overflow should catch this exception
    and decide whether to truncate, drop, or log-and-continue.
    """


def safe_serialize_state(state: dict) -> str:
    """
    JSON-serialize *state* with non-serializable value stripping.

    Any value that the standard JSON encoder cannot handle (generators,
    callables, custom objects without __dict__, etc.) is replaced with a
    descriptive placeholder string:

        "<non-serializable: <typename>>"

    Each replacement is logged at DEBUG level so developers can trace which
    keys are being silently dropped.

    Returns:
        A JSON string representing the (possibly stripped) state.
    """
    def _safe_default(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        type_name = type(obj).__name__
        logger.debug(
            f"[state_serializer] Replacing non-serializable {type_name} with placeholder"
        )
        return f"<non-serializable: {type_name}>"

    return json.dumps(state, default=_safe_default)


def check_state_size(state: dict, key: str, max_bytes: int) -> None:
    """
    Raise *StateOverflowError* if *state[key]* serializes to more than
    *max_bytes* bytes.

    If *key* is not present in *state* the check is a no-op (nothing to
    guard against).

    Args:
        state:      The GraphState (or any dict) to inspect.
        key:        The key whose value should be size-checked.
        max_bytes:  Maximum permitted size in bytes.

    Raises:
        StateOverflowError: When the serialized size of *state[key]* exceeds
            *max_bytes*.
    """
    if key not in state:
        return
    value = state[key]

    serialized = json.dumps(value).encode()
    actual_bytes = len(serialized)

    if actual_bytes > max_bytes:
        raise StateOverflowError(
            f"State key '{key}' is {actual_bytes} bytes, "
            f"which exceeds the limit of {max_bytes} bytes."
        )
