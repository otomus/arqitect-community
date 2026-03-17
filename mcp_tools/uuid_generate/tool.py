"""Generate a universally unique identifier."""

import uuid


def run(version: str = "4") -> str:
    """Generate a UUID."""
    if version == "4":
        return str(uuid.uuid4())
    if version == "1":
        return str(uuid.uuid1())
    raise ValueError(f"Unsupported UUID version: {version}. Use 1 or 4.")
