"""Decode a base64 string back to plain text."""

import base64


def run(input: str) -> str:
    """Decode a base64 string."""
    return base64.b64decode(input.encode("ascii")).decode("utf-8")
