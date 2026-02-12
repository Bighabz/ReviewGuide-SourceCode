"""Circuit Breaker - Skip APIs that have failed repeatedly.

States: CLOSED (normal) -> OPEN (skip) -> CLOSED (after timeout)

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
