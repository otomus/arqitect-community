"""Compute a cryptographic hash of a string."""

import hashlib

SUPPORTED_ALGORITHMS = ("md5", "sha1", "sha256", "sha512")


def run(input: str, algorithm: str = "sha256") -> str:
    """Compute a hash of the input string."""
    algo = algorithm.lower()
    if algo not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use one of: {', '.join(SUPPORTED_ALGORITHMS)}")
    h = hashlib.new(algo)
    h.update(input.encode("utf-8"))
    return h.hexdigest()
