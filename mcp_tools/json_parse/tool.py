"""Parse a JSON string into a structured object."""

import json


def run(text: str) -> str:
    """Parse a JSON string and return the structured representation."""
    parsed = json.loads(text)
    return json.dumps(parsed, indent=2, ensure_ascii=False)
