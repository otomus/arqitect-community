"""List all connected IoT devices on the gateway."""

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


def run(device_host: str = "") -> str:
    """List all devices registered on the IoT gateway.

    Calls GET {device_host}/api/v1/devices to retrieve the full device list.

    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string with a list of connected devices.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
    url = f"{host}/api/v1/devices"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    devices = data if isinstance(data, list) else data.get("devices", [])

    return json.dumps({
        "host": host,
        "count": len(devices),
        "devices": devices,
    }, indent=2)
