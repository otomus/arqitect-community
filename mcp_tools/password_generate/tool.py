"""Generate a cryptographically secure password."""

import secrets
import string

CHARSETS = {
    "alphanumeric": string.ascii_letters + string.digits,
    "ascii": string.ascii_letters + string.digits + string.punctuation,
    "digits": string.digits,
    "hex": string.hexdigits[:16],
}


def run(length: int = 20, charset: str = "ascii") -> str:
    """Generate a secure random password."""
    chars = CHARSETS.get(charset)
    if chars is None:
        raise ValueError(f"Unknown charset: {charset}. Use one of: {', '.join(CHARSETS)}")
    if length < 1 or length > 256:
        raise ValueError("Length must be between 1 and 256")
    return "".join(secrets.choice(chars) for _ in range(length))
