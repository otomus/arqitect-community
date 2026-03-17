"""Set the state of a smart lock (lock or unlock)."""

import json
import os

try:
    import requests
except ImportError:
    requests = None

VALID_STATES = {"lock", "unlock"}


def _get_host(device_host: str) -> str:
    """Resolve the IoT gateway host from parameter or environment."""
    host = device_host or os.environ.get("SENTIENT_IOT_HOST", "")
    if not host:
        raise RuntimeError("No device_host provided and SENTIENT_IOT_HOST is not set")
    return host.rstrip("/")


def run(device_id: str, state: str, device_host: str = "") -> str:
    """Set a smart lock to the locked or unlocked state.

    Calls POST {device_host}/api/v1/locks/{device_id} with the desired
    state in the request body.

    @param device_id: Unique identifier of the smart lock.
    @param state: Desired state -- must be 'lock' or 'unlock'.
    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string confirming the lock state change.
    @throws ValueError: If the state is not 'lock' or 'unlock'.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    state_lower = state.lower()
    if state_lower not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'. Must be one of: {', '.join(sorted(VALID_STATES))}")

    host = _get_host(device_host)
    url = f"{host}/api/v1/locks/{device_id}"

    response = requests.post(url, json={"state": state_lower}, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "state": state_lower,
        "previous_state": data.get("previous_state"),
        "status": data.get("status", "ok"),
    }, indent=2)
