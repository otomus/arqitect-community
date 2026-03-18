"""Unified password management: generate, get, and store passwords.

Generate uses the secrets module for cryptographic randomness.
Get/store use a JSON vault file at ~/.sentient_vault.json.
If SENTIENT_VAULT_KEY env var is set, the vault is encrypted with Fernet.
Otherwise, the vault is stored as plaintext JSON.
"""

import base64
import hashlib
import json
import os
import secrets
import string
import sys
from datetime import datetime, timezone

VAULT_FILE = os.path.expanduser("~/.sentient_vault.json")
VAULT_KEY_ENV = "SENTIENT_VAULT_KEY"

VALID_OPERATIONS = {"generate", "get", "store"}

CHARSETS = {
    "alphanumeric": string.ascii_letters + string.digits,
    "ascii": string.ascii_letters + string.digits + string.punctuation,
    "digits": string.digits,
    "hex": string.hexdigits[:16],
}


def _get_fernet():
    """Get a Fernet cipher if the vault key env var is set.

    Returns:
        Fernet instance or None if key is not configured.
    """
    key = os.environ.get(VAULT_KEY_ENV, "")
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None
    # Derive a 32-byte key from the env var using SHA-256, then base64 encode
    derived = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def _load_vault() -> dict:
    """Load the vault data from disk.

    Returns:
        Dict mapping vault namespaces to their entries.
    """
    if not os.path.exists(VAULT_FILE):
        return {}

    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    fernet = _get_fernet()
    if fernet and raw.strip():
        try:
            decrypted = fernet.decrypt(raw.strip().encode()).decode("utf-8")
            return json.loads(decrypted)
        except Exception:
            # Fall back to plaintext parse if decryption fails
            pass

    return json.loads(raw) if raw.strip() else {}


def _save_vault(data: dict) -> None:
    """Persist vault data to disk, optionally encrypted.

    Args:
        data: Dict mapping vault namespaces to their entries.
    """
    payload = json.dumps(data, indent=2)
    fernet = _get_fernet()
    if fernet:
        payload = fernet.encrypt(payload.encode()).decode("utf-8")

    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        f.write(payload)


def _handle_generate(params: dict) -> dict:
    """Generate a cryptographically secure random password.

    Args:
        params: Optionally contains 'length' and 'charset'.

    Returns:
        Dict with the generated password.
    """
    length = int(params.get("length", "20"))
    charset = params.get("charset", "ascii")

    chars = CHARSETS.get(charset)
    if chars is None:
        raise ValueError(f"Unknown charset: {charset}. Use one of: {', '.join(CHARSETS)}")
    if length < 1 or length > 256:
        raise ValueError("Length must be between 1 and 256")

    password = "".join(secrets.choice(chars) for _ in range(length))
    return {"status": "generated", "password": password, "length": length, "charset": charset}


def _handle_get(params: dict) -> dict:
    """Retrieve a password from the vault.

    Args:
        params: Must contain 'name'. Optionally 'vault'.

    Returns:
        Dict with the found entry.
    """
    name = params.get("name")
    if not name:
        raise ValueError("name is required for get operation")

    vault_name = params.get("vault", "default")
    data = _load_vault()
    vault_entries = data.get(vault_name, {})

    if name not in vault_entries:
        raise ValueError(f"Entry not found: '{name}' in vault '{vault_name}'")

    entry = vault_entries[name]
    return {"status": "found", "name": name, "vault": vault_name, "value": entry["value"]}


def _handle_store(params: dict) -> dict:
    """Store a password in the vault.

    Args:
        params: Must contain 'name' and 'value'. Optionally 'vault'.

    Returns:
        Dict with status and stored entry metadata.
    """
    name = params.get("name")
    value = params.get("value")
    if not name:
        raise ValueError("name is required for store operation")
    if not value:
        raise ValueError("value is required for store operation")

    vault_name = params.get("vault", "default")
    data = _load_vault()

    if vault_name not in data:
        data[vault_name] = {}

    data[vault_name][name] = {
        "value": value,
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_vault(data)

    encrypted = bool(_get_fernet())
    return {
        "status": "stored",
        "name": name,
        "vault": vault_name,
        "encrypted": encrypted,
    }


HANDLERS = {
    "generate": _handle_generate,
    "get": _handle_get,
    "store": _handle_store,
}


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        operation = params.get("operation", "")
        if operation not in VALID_OPERATIONS:
            raise ValueError(
                f"Invalid operation: '{operation}'. Must be one of: {', '.join(sorted(VALID_OPERATIONS))}"
            )
        handler = HANDLERS[operation]
        result = handler(params)
        resp = {"id": req.get("id"), "result": json.dumps(result, indent=2)}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
