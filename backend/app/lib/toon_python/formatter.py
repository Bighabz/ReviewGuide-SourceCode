"""
Output formatting and indentation for TOON format.
"""


from .constants import EncodeOptions


class OutputFormatter:
    """Handles indentation, delimiters, and final output formatting."""

    def __init__(self, options: EncodeOptions):
        self.indent_size = options.indent
        self.delimiter = options.delimiter.value
        self.length_marker = options.length_marker

    def format_object_line(self, key: str, depth: int) -> str:
        """Format a line for an object key."""
        return f"{key}:"

    def format_primitive_line(self, key: str, value: str, depth: int) -> str:
        """Format a line for a primitive value."""
        return f"{key}: {value}"

    def format_array_header(self, key: str, count: int, headers: list[str] | None) -> str:
        """Format an array header line."""
        prefix = f"{self.length_marker}" if self.length_marker else ""

        if headers:
            # Tabular format: key[N]{f1,f2}:
            header_str = ','.join(headers)
            return f"{key}{prefix}[{count}]{{{header_str}}}:"
        else:
            # Inline format: key[N]: v1,v2
            return f"{key}{prefix}[{count}]:"

    def format_list_item(self, item: str, depth: int) -> str:
        """Format a list item."""
        return f"- {item}"
