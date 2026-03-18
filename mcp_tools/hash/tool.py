"""Compute or verify cryptographic hashes."""

import hashlib
import hmac
import json

SUPPORTED_ALGORITHMS = ("md5", "sha1", "sha256", "sha512")


def run(input: str, algorithm: str, operation: str, hash: str = "") -> str:
    """Compute a hash or verify an input against an expected hash.

    @param input: String to hash.
    @param algorithm: Hash algorithm (md5, sha1, sha256, sha512).
    @param operation: 'compute' to generate a hash, 'verify' to check against expected.
    @param hash: Expected hash for verification (required for verify).
    @returns The hex digest or a JSON verification result.
    @throws ValueError: If the operation or algorithm is invalid.
    """
    if operation == "compute":
        return _compute(input, algorithm)
    if operation == "verify":
        return _verify(input, algorithm, hash)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'compute' or 'verify'.")


def _compute(input: str, algorithm: str) -> str:
    """Compute a hash of the input string."""
    algo = algorithm.lower()
    if algo not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. Use one of: {', '.join(SUPPORTED_ALGORITHMS)}"
        )
    h = hashlib.new(algo)
    h.update(input.encode("utf-8"))
    return h.hexdigest()


def _verify(input: str, algorithm: str, expected_hash: str) -> str:
    """Verify that the hash of input matches the expected hash."""
    h = hashlib.new(algorithm)
    h.update(input.encode("utf-8"))
    computed = h.hexdigest()
    matches = hmac.compare_digest(computed, expected_hash.lower())
    return json.dumps({"matches": matches, "computed": computed, "expected": expected_hash.lower()})
