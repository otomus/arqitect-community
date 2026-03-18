"""Set or read a smart thermostat via the IoT gateway."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(device_id: str, operation: str, target: str = "", mode: str = "") -> str:
    """Control or query a smart thermostat.

    @param device_id: Unique identifier of the thermostat.
    @param operation: 'set' to change settings, 'read' to get current state.
    @param target: Target temperature (set only).
    @param mode: Operating mode like heat, cool, auto (set only).
    @returns JSON string with thermostat readings and settings.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read_thermostat(device_id)
    if operation == "set":
        return _set_thermostat(device_id, target, mode)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'set' or 'read'.")


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")


def _read_thermostat(device_id: str) -> str:
    """Read the thermostat's current temperature and target settings."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/thermostats/{device_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "current_temperature": data.get("current_temperature"),
        "target_temperature": data.get("target_temperature"),
        "unit": data.get("unit", "celsius"),
        "mode": data.get("mode", "auto"),
        "humidity": data.get("humidity"),
        "status": data.get("status", "ok"),
    }, indent=2)


def _set_thermostat(device_id: str, target: str, mode: str) -> str:
    """Set the thermostat's target temperature and/or operating mode."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/thermostats/{device_id}"

    body: dict = {}
    if target:
        body["target_temperature"] = float(target)
    if mode:
        body["mode"] = mode

    response = requests.post(url, json=body, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "target_temperature": data.get("target_temperature"),
        "mode": data.get("mode"),
        "status": data.get("status", "ok"),
    }, indent=2)
