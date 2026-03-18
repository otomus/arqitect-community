"""Encode or decode base64 strings."""

import base64


def run(input: str, operation: str) -> str:
    """Encode or decode a base64 string based on the operation parameter.

    @param input: String to encode, or base64 string to decode.
    @param operation: 'encode' to convert to base64, 'decode' to convert from base64.
    @returns The encoded or decoded string.
    @throws ValueError: If the operation is not 'encode' or 'decode'.
    """
    if operation == "encode":
        return base64.b64encode(input.encode("utf-8")).decode("ascii")
    if operation == "decode":
        return base64.b64decode(input.encode("ascii")).decode("utf-8")
    raise ValueError(f"Invalid operation '{operation}'. Must be 'encode' or 'decode'.")
