"""Get the status of a connected IoT device."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def _get_host(device_host: str) -> str:
    """Resolve the IoT gateway host from parameter or environment."""
    host = device_host or os.environ.get("SENTIENT_IOT_HOST", "")
    if not host:
        raise RuntimeError("No device_host provided and SENTIENT_IOT_HOST is not set")
    return host.rstrip("/")


def run(device_id: str, device_host: str = "") -> str:
    """Get the current status of a device from the IoT gateway.

    Calls GET {device_host}/api/v1/devices/{device_id} to retrieve
    the device status including connectivity, battery, and firmware info.

    @param device_id: Unique identifier of the device.
    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string with the device status.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
    url = f"{host}/api/v1/devices/{device_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "name": data.get("name", ""),
        "status": data.get("status", "unknown"),
        "online": data.get("online", False),
        "battery": data.get("battery"),
        "firmware": data.get("firmware", ""),
        "last_seen": data.get("last_seen", ""),
    }, indent=2)
