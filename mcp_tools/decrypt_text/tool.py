"""Decrypt text encrypted by encrypt_text."""

import base64
import hashlib
import hmac


def _derive_key(key: str) -> bytes:
    """Derive a 32-byte key from a passphrase."""
    return hashlib.sha256(key.encode("utf-8")).digest()


def run(ciphertext: str, key: str) -> str:
    """Decrypt text encrypted with encrypt_text."""
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
