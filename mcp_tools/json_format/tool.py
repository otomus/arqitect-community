"""Format a JSON object as a pretty-printed string."""

import json


def run(text: str, indent: int = 2) -> str:
    """Format a JSON string with indentation."""
    parsed = json.loads(text)
    return json.dumps(parsed, indent=indent, ensure_ascii=False, sort_keys=True)
