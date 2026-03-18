"""Encrypt or decrypt text using a symmetric key."""

import base64
import hashlib
import hmac
import os


def run(text: str, key: str, operation: str) -> str:
    """Encrypt or decrypt text using a passphrase-derived key.

    @param text: Plaintext to encrypt, or base64 ciphertext to decrypt.
    @param key: Passphrase used for key derivation.
    @param operation: 'encrypt' or 'decrypt'.
    @returns Encrypted base64 payload or decrypted plaintext.
    @throws ValueError: If the operation is invalid or decryption fails.
    """
    if operation == "encrypt":
        return _encrypt(text, key)
    if operation == "decrypt":
        return _decrypt(text, key)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'encrypt' or 'decrypt'.")


def _derive_key(key: str) -> bytes:
    """Derive a 32-byte key from a passphrase."""
    return hashlib.sha256(key.encode("utf-8")).digest()


def _encrypt(text: str, key: str) -> str:
    """Encrypt text with XOR-based stream cipher and HMAC authentication."""
    derived = _derive_key(key)
    iv = os.urandom(16)
    plaintext = text.encode("utf-8")
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len] * pad_len)
    key_stream = (derived + iv) * ((len(padded) // 48) + 1)
    encrypted = bytes(a ^ b for a, b in zip(padded, key_stream[:len(padded)]))
    mac = hmac.new(derived, iv + encrypted, hashlib.sha256).digest()
    payload = base64.b64encode(iv + encrypted + mac).decode("ascii")
    return payload


def _decrypt(ciphertext: str, key: str) -> str:
    """Decrypt text encrypted with the encrypt operation."""
    derived = _derive_key(key)
    raw = base64.b64decode(ciphertext)
    iv = raw[:16]
    mac_received = raw[-32:]
    encrypted = raw[16:-32]
    mac_computed = hmac.new(derived, iv + encrypted, hashlib.sha256).digest()
    if not hmac.compare_digest(mac_received, mac_computed):
        raise ValueError("Decryption failed: invalid key or corrupted data")
    key_stream = (derived + iv) * ((len(encrypted) // 48) + 1)
    decrypted = bytes(a ^ b for a, b in zip(encrypted, key_stream[:len(encrypted)]))
    pad_len = decrypted[-1]
    return decrypted[:-pad_len].decode("utf-8")
