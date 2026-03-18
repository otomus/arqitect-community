"""Parse, format, or query JSON data."""

import json


def run(input: str, operation: str, query: str = "", indent: str = "") -> str:
    """Parse, pretty-print, or query a JSON string.

    @param input: JSON string to process.
    @param operation: 'parse' to validate and pretty-print, 'format' to sort keys and indent, 'query' to extract via dot-notation.
    @param query: Dot-notation path for the query operation.
    @param indent: Number of spaces for indentation (format only, defaults to 2).
    @returns Processed JSON string or extracted value.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "parse":
        return _parse(input)
    if operation == "format":
        return _format(input, indent)
    if operation == "query":
        return _query(input, query)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'parse', 'format', or 'query'.")


def _parse(text: str) -> str:
    """Parse a JSON string and return a pretty-printed representation."""
    parsed = json.loads(text)
    return json.dumps(parsed, indent=2, ensure_ascii=False)


def _format(text: str, indent: str) -> str:
    """Format a JSON string with sorted keys and indentation."""
    indent_value = int(indent) if indent else 2
    parsed = json.loads(text)
    return json.dumps(parsed, indent=indent_value, ensure_ascii=False, sort_keys=True)


def _query(text: str, query: str) -> str:
    """Extract a value from JSON using a dot-notation path."""
    data = json.loads(text)
    parts = query.split(".")
    current = data
    for part in parts:
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(f"Cannot traverse into {type(current).__name__} with key '{part}'")
    if isinstance(current, (dict, list)):
        return json.dumps(current, indent=2, ensure_ascii=False)
    return str(current)
