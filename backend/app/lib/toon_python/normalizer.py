"""
Type normalization for TOON encoding.
"""

import base64
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from .types import JsonPrimitive, JsonValue


class ValueNormalizer:
    """Converts Python types to JSON-compatible representations."""

    def __init__(self) -> None:
        self.type_handlers: dict[type, Callable] = {
            datetime: self._normalize_datetime,
            date: self._normalize_date,
            Decimal: self._normalize_decimal,
            UUID: self._normalize_uuid,
            bytes: self._normalize_bytes,
            set: self._normalize_set,
            frozenset: self._normalize_frozenset,
        }
        self._visited: set[int] = set()

    def normalize(self, value: Any) -> JsonValue:
        """Convert Python value to JSON-compatible representation."""
        # Reset visited for each normalization
        self._visited.clear()
        return self._normalize_with_circular_check(value)

    def _normalize_with_circular_check(self, value: Any) -> JsonValue:
        """Normalize with circular reference detection."""
        # Handle None
        if value is None:
            return None

        # Handle primitive types
        if isinstance(value, (str, int, bool)):
            return value

        # Handle float with special cases
        if isinstance(value, float):
            return self._normalize_number(value)

        # Check for circular references in collections
        if isinstance(value, (dict, list, tuple)):
            obj_id = id(value)
            if obj_id in self._visited:
                from .encoder import CircularReferenceError
                raise CircularReferenceError("Circular reference detected during normalization")
            self._visited.add(obj_id)

        try:
            # Handle collections
            if isinstance(value, dict):
                return {k: self._normalize_with_circular_check(v) for k, v in value.items()}

            if isinstance(value, (list, tuple)):
                return [self._normalize_with_circular_check(item) for item in value]
        finally:
            # Clean up visited set for collections
            if isinstance(value, (dict, list, tuple)):
                self._visited.discard(id(value))

        # Handle custom types
        value_type = type(value)
        if value_type in self.type_handlers:
            result = self.type_handlers[value_type](value)
            return result  # type: ignore[no-any-return]

        # Default to None for unsupported types
        return None

    def _normalize_number(self, value: int | float) -> JsonPrimitive:
        """Normalize numeric values with special cases."""
        if isinstance(value, float):
            # Convert -0 to 0 (including -0.0)
            if value == 0 and str(value).startswith('-'):
                return 0
            # Convert NaN and infinities to null
            if value != value or value in (float('inf'), float('-inf')):
                return None
        return value

    def _normalize_datetime(self, value: datetime) -> str:
        """Convert datetime to ISO string."""
        return value.isoformat()

    def _normalize_date(self, value: date) -> str:
        """Convert date to ISO string."""
        return value.isoformat()

    def _normalize_decimal(self, value: Decimal) -> str:
        """Convert Decimal to string."""
        return str(value)

    def _normalize_uuid(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)

    def _normalize_bytes(self, value: bytes) -> str:
        """Convert bytes to Base64 string."""
        return base64.b64encode(value).decode('ascii')

    def _normalize_set(self, value: set) -> list[JsonValue]:
        """Convert set to list."""
        return [self.normalize(item) for item in value]

    def _normalize_frozenset(self, value: frozenset) -> list[JsonValue]:
        """Convert frozenset to list."""
        return [self.normalize(item) for item in value]
