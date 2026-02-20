"""
Constants and configuration for TOON encoding.
"""

from dataclasses import dataclass
from enum import Enum


class Delimiter(Enum):
    """Supported delimiters for array value separation."""
    COMMA = ','
    TAB = '\t'
    PIPE = '|'


@dataclass
class EncodeOptions:
    """Configuration options for TOON encoding."""
    indent: int = 2
    delimiter: Delimiter = Delimiter.COMMA
    length_marker: str | None = None  # '#' or None


class ArrayType(Enum):
    """Array encoding strategies."""
    INLINE = "inline"      # Primitive arrays: tags[3]: admin,ops,dev
    TABULAR = "tabular"    # Uniform objects: items[2]{sku,qty,price}:
    LIST = "list"          # Mixed/nested: items[3]: - item1 - item2
