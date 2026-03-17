"""Test a regex pattern against text and return matches."""

import json
import re


def run(pattern: str, text: str) -> str:
    """Find all matches of a regex pattern in the text."""
    matches = re.findall(pattern, text)
    return json.dumps({"pattern": pattern, "match_count": len(matches), "matches": matches}, indent=2)
