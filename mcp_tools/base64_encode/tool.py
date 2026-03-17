"""Encode a string to base64."""

import base64


def run(input: str) -> str:
    """Encode the input string as base64."""
    return base64.b64encode(input.encode("utf-8")).decode("ascii")
