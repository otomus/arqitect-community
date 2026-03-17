"""Query a JSON object using dot-notation path."""

import json


def run(text: str, query: str) -> str:
    """Extract a value from JSON using dot-notation path."""
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
