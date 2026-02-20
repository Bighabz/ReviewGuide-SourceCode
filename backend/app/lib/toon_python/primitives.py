"""
Primitive encoding and quoting for TOON format.
"""

from .types import JsonPrimitive


class PrimitiveEncoder:
    """Encodes primitive values with proper quoting."""

    def __init__(self) -> None:
        self.escape_chars = {'\\', '"', '\n', '\r', '\t', '\b', '\f'}

    def encode_primitive(self, value: JsonPrimitive, delimiter: str) -> str:
        """Encode a primitive value with proper quoting."""
        if value is None:
            return 'null'

        if isinstance(value, bool):
            return 'true' if value else 'false'

        if isinstance(value, (int, float)):
            return str(value)

        # Handle strings
        return self.encode_string(value, delimiter)

    def encode_string(self, value: str, delimiter: str) -> str:
        """Encode a string value with proper quoting."""
        if self.needs_quotes(value, delimiter):
            escaped = self.escape_string(value)
            return f'"{escaped}"'
        return value

    def escape_string(self, value: str) -> str:
        """Escape special characters in string."""
        result = []
        for char in value:
            if char == '\\':
                result.append('\\\\')
            elif char == '"':
                result.append('\\"')
            elif char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            elif char == '\b':
                result.append('\\b')
            elif char == '\f':
                result.append('\\f')
            else:
                result.append(char)
        return ''.join(result)

    def needs_quotes(self, value: str, delimiter: str) -> bool:
        """Determine if a string needs quotes."""
        # Empty string
        if not value:
            return True

        # Contains special characters
        special_chars = {delimiter, ':', '"', '\\', '\n', '\r', '\t'}
        if any(char in special_chars for char in value):
            return True

        # Leading or trailing spaces
        if value != value.strip():
            return True

        # Looks like boolean/number/null
        if value.lower() in ('true', 'false', 'null'):
            return True

        # Looks like a number
        if self._looks_like_number(value):
            return True

        # Starts with "- " (list-like)
        if value.startswith('- '):
            return True

        # Looks like structural token
        if self._looks_like_structural_token(value):
            return True

        return False

    def _looks_like_number(self, value: str) -> bool:
        """Check if string looks like a number."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _looks_like_structural_token(self, value: str) -> bool:
        """Check if string looks like a structural token."""
        import re

        # [N] pattern
        if re.match(r'^\[\d+\]$', value):
            return True

        # {key} pattern
        if re.match(r'^\{[^}]+\}$', value):
            return True

        # [N]: x,y pattern
        if re.match(r'^\[\d+\]: .+$', value):
            return True

        return False
