"""Find and replace text using a regular expression."""

import re


def run(pattern: str, replacement: str, text: str) -> str:
    """Replace all matches of a regex pattern in the text."""
    return re.sub(pattern, replacement, text)
