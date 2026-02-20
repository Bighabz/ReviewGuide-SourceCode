"""
Type definitions for TOON encoding.
"""


# Primitive types
JsonPrimitive = str | int | float | bool | None

# Complex types
JsonObject = dict[str, "JsonValue"]
JsonArray = list["JsonValue"]

# Union type
JsonValue = JsonPrimitive | JsonObject | JsonArray
