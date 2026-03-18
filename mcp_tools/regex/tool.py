"""Match or replace text using regular expressions."""

import json
import re


def run(pattern: str, text: str, operation: str, replacement: str = "") -> str:
    """Find matches or perform replacements using a regex pattern.

    @param pattern: Regular expression pattern.
    @param text: Text to search or transform.
    @param operation: 'match' to find all matches, 'replace' to substitute.
    @param replacement: Replacement string (required for replace).
    @returns JSON match results or the transformed text.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "match":
        matches = re.findall(pattern, text)
        return json.dumps(
            {"pattern": pattern, "match_count": len(matches), "matches": matches},
            indent=2,
        )
    if operation == "replace":
        return re.sub(pattern, replacement, text)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'match' or 'replace'.")
