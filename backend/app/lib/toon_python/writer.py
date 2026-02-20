"""
Line writing utilities for streaming output.
"""



class LineWriter:
    """Streaming output to avoid memory buildup."""

    def __init__(self, indent_size: int = 2):
        self.lines: list[str] = []
        self.indent_size = indent_size

    def push(self, depth: int, line: str) -> None:
        """Add a line with proper indentation."""
        indent = ' ' * (depth * self.indent_size)
        self.lines.append(f"{indent}{line}")

    def to_string(self) -> str:
        """Convert accumulated lines to final string."""
        return '\n'.join(self.lines)
