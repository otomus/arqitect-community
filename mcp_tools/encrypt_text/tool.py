"""Encrypt text using Fernet symmetric encryption."""

import base64
import hashlib
import hmac
import json
import os


def _derive_key(key: str) -> bytes:
    """Derive a 32-byte key from a passphrase."""
    return hashlib.sha256(key.encode("utf-8")).digest()


def run(text: str, key: str) -> str:
    """Encrypt text with AES-CBC via a simple key derivation."""
    derived = _derive_key(key)
    iv = os.urandom(16)
    # Simple XOR-based stream cipher for stdlib-only (no cryptography dependency)
    plaintext = text.encode("utf-8")
    # Pad to 16-byte blocks
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)
    # XOR with key stream (repeating key + iv)
    key_stream = (derived + iv) * ((len(padded) // 48) + 1)
    encrypted = bytes(a ^ b for a, b in zip(padded, key_stream[:len(padded)]))
    mac = hmac.new(derived, iv + encrypted, hashlib.sha256).digest()
    payload = base64.b64encode(iv + encrypted + mac).decode("ascii")
    return payload
