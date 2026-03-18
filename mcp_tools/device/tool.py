"""Get device status or list all connected IoT devices."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(operation: str, device_id: str = "", network: str = "") -> str:
    """Query a device's status or list all devices on the IoT gateway.

    @param operation: 'status' to get one device, 'list' to enumerate all.
    @param device_id: Device identifier (required for status).
    @param network: Filter by network (optional, list only).
    @returns JSON string with device information.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "status":
        return _device_status(device_id)
    if operation == "list":
        return _device_list(network)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'status' or 'list'.")


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")


def _device_status(device_id: str) -> str:
    """Get the current status of a device."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
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


def _device_list(network: str) -> str:
    """List all devices registered on the IoT gateway."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/devices"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    devices = data if isinstance(data, list) else data.get("devices", [])

    if network:
        devices = [d for d in devices if d.get("network") == network]

    return json.dumps({
        "host": host,
        "count": len(devices),
        "devices": devices,
    }, indent=2)
