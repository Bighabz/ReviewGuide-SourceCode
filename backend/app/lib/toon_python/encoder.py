"""
Main orchestration logic for TOON encoding.
"""

from typing import Any

from .constants import ArrayType, EncodeOptions
from .formatter import OutputFormatter
from .normalizer import ValueNormalizer
from .primitives import PrimitiveEncoder
from .types import JsonArray, JsonObject, JsonValue
from .writer import LineWriter


class ToonEncodingError(Exception):
    """Base exception for TOON encoding errors."""

    pass


class CircularReferenceError(ToonEncodingError):
    """Raised when circular references are detected in input data."""

    pass


class DatasetTooLargeError(ToonEncodingError):
    """Raised when input data exceeds 10MB size limit."""

    pass


class NonSerializableError(ToonEncodingError):
    """Raised when input contains non-serializable objects."""

    pass


class ArrayAnalyzer:
    """Analyzes arrays to determine optimal encoding strategy."""

    def __init__(self, uniform_threshold: int = 2):
        self.uniform_threshold = uniform_threshold

    def analyze_array(self, arr: JsonArray) -> ArrayType:
        """Determine the optimal encoding strategy for an array."""
        if not arr:
            return ArrayType.LIST

        if self._is_uniform_objects(arr):
            return ArrayType.TABULAR

        if self._is_primitives_only(arr):
            return ArrayType.INLINE

        return ArrayType.LIST

    def is_uniform_objects(self, arr: JsonArray) -> bool:
        """Check if array contains uniform objects."""
        return self._is_uniform_objects(arr)

    def get_tabular_headers(self, arr: JsonArray) -> list[str]:
        """Get headers for tabular array encoding."""
        if not arr or not isinstance(arr[0], dict):
            return []

        return list(arr[0].keys())

    def _is_uniform_objects(self, arr: JsonArray) -> bool:
        """Check if all elements are objects with identical key sets."""
        if len(arr) < self.uniform_threshold:
            return False

        # All elements must be objects
        if not all(isinstance(item, dict) for item in arr):
            return False

        # Get key set from first object
        first_obj = arr[0]
        if not isinstance(first_obj, dict):
            return False
        first_keys = set(first_obj.keys())

        # All objects must have identical key sets
        for item in arr[1:]:
            if not isinstance(item, dict):
                return False
            if set(item.keys()) != first_keys:
                return False

        # All values must be primitives (no nested objects/arrays)
        for obj in arr:
            if not isinstance(obj, dict):
                return False
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    return False

        return True

    def _is_primitives_only(self, arr: JsonArray) -> bool:
        """Check if array contains only primitive values."""
        return all(not isinstance(item, (dict, list)) for item in arr)


class ToonEncoder:
    """Main orchestration component for TOON encoding."""

    def __init__(self, options: EncodeOptions):
        self.options = options
        self.normalizer = ValueNormalizer()
        self.primitive_encoder = PrimitiveEncoder()
        self.formatter = OutputFormatter(options)
        self.writer = LineWriter(options.indent)
        self.array_analyzer = ArrayAnalyzer()
        self._visited: set[int] = set()  # For circular reference detection

    def encode(self, data: Any) -> str:
        """Convert data to TOON format."""
        # Reset state
        self._visited.clear()
        self.writer = LineWriter(self.options.indent)

        # Check dataset size (rough estimate)
        self._check_dataset_size(data)

        # Normalize and encode
        normalized = self.normalizer.normalize(data)
        self._encode_value(normalized, depth=0)

        return self.writer.to_string()

    def _encode_value(
        self, value: JsonValue, depth: int, key: str | None = None
    ) -> None:
        """Encode a value with proper context."""
        if isinstance(value, dict):
            self._encode_object(value, depth, key)
        elif isinstance(value, list):
            self._encode_array(value, key, depth)
        else:
            self._encode_primitive(key, value, depth)

    def _encode_object(
        self, obj: JsonObject, depth: int, key: str | None = None
    ) -> None:
        """Encode an object."""
        if key is not None:
            line = self.formatter.format_object_line(key, depth)
            self.writer.push(depth, line)
            depth += 1

        # Check for circular reference
        obj_id = id(obj)
        if obj_id in self._visited:
            raise CircularReferenceError(f"Circular reference detected at key: {key}")
        self._visited.add(obj_id)

        # Encode each key-value pair
        for k, v in obj.items():
            self._encode_value(v, depth, k)

        self._visited.remove(obj_id)

    def _encode_array(self, arr: JsonArray, key: str | None, depth: int) -> None:
        """Encode an array with optimal strategy."""
        if not arr:
            # Empty array
            if key is not None:
                line = self.formatter.format_array_header(key, 0, None)
                self.writer.push(depth, line)
            return

        # Determine encoding strategy
        array_type = self.array_analyzer.analyze_array(arr)

        if array_type == ArrayType.INLINE:
            self._encode_inline_array(arr, key, depth)
        elif array_type == ArrayType.TABULAR:
            self._encode_tabular_array(arr, key, depth)
        else:
            self._encode_list_array(arr, key, depth)

    def _encode_inline_array(self, arr: JsonArray, key: str | None, depth: int) -> None:
        """Encode array as inline format."""
        # Encode all values as primitives
        encoded_values = []
        for item in arr:
            if isinstance(item, (dict, list)):
                # Fall back to list format for nested structures
                self._encode_list_array(arr, key, depth)
                return
            encoded = self.primitive_encoder.encode_primitive(
                item, self.formatter.delimiter
            )
            encoded_values.append(encoded)

        # Format as inline
        values_str = self.formatter.delimiter.join(encoded_values)
        if key is not None:
            line = self.formatter.format_array_header(key, len(arr), None)
            # Put values on the same line as the header for inline arrays
            self.writer.push(depth, f"{line} {values_str}")
        else:
            self.writer.push(depth, values_str)

    def _encode_tabular_array(
        self, arr: JsonArray, key: str | None, depth: int
    ) -> None:
        """Encode array as tabular format."""
        headers = self.array_analyzer.get_tabular_headers(arr)

        if key is not None:
            line = self.formatter.format_array_header(key, len(arr), headers)
            self.writer.push(depth, line)
            depth += 1

        # Encode each row
        for obj in arr:
            if not isinstance(obj, dict):
                continue
            row_values = []
            for header in headers:
                value = obj[header]
                if isinstance(value, (dict, list)):
                    # This shouldn't happen in tabular format, but handle gracefully
                    encoded = str(value)
                else:
                    encoded = self.primitive_encoder.encode_primitive(
                        value, self.formatter.delimiter
                    )
                row_values.append(encoded)

            row_str = self.formatter.delimiter.join(row_values)
            self.writer.push(depth, row_str)

    def _encode_list_array(self, arr: JsonArray, key: str | None, depth: int) -> None:
        """Encode array as list format."""
        if key is not None:
            line = self.formatter.format_array_header(key, len(arr), None)
            self.writer.push(depth, line)
            depth += 1

        # Encode each item
        for item in arr:
            if isinstance(item, dict):
                # Nested object - encode with proper list formatting
                for k, v in item.items():
                    self._encode_value(v, depth, k)
            elif isinstance(item, list):
                # Nested list - encode as list item
                self._encode_array(item, None, depth)
            else:
                # Primitive item
                encoded = self.primitive_encoder.encode_primitive(
                    item, self.formatter.delimiter
                )
                line = self.formatter.format_list_item(encoded, depth)
                self.writer.push(depth, line)

    def _encode_primitive(self, key: str | None, value: JsonValue, depth: int) -> None:
        """Encode a primitive value."""
        if isinstance(value, (dict, list)):
            # This shouldn't happen for primitives, but handle gracefully
            encoded = str(value)
        else:
            encoded = self.primitive_encoder.encode_primitive(
                value, self.formatter.delimiter
            )

        if key is not None:
            line = self.formatter.format_primitive_line(key, encoded, depth)
            self.writer.push(depth, line)
        else:
            self.writer.push(depth, encoded)

    def _check_dataset_size(self, data: Any) -> None:
        """Rough check if dataset is too large."""
        try:
            import json

            size = len(json.dumps(data, default=str))
            if size > 10 * 1024 * 1024:  # 10MB
                raise DatasetTooLargeError(
                    f"Dataset size ({size} bytes) exceeds 10MB limit"
                )
        except (TypeError, ValueError):
            # If we can't serialize, let the normalizer handle it
            pass
