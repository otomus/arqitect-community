"""Verify that input matches an expected hash."""

import hashlib
import hmac
import json


def run(input: str, hash: str, algorithm: str = "sha256") -> str:
    """Verify that the hash of input matches the expected hash."""
    h = hashlib.new(algorithm)
    h.update(input.encode("utf-8"))
    computed = h.hexdigest()
    matches = hmac.compare_digest(computed, hash.lower())
    return json.dumps({"matches": matches, "computed": computed, "expected": hash.lower()})
