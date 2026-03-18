"""Set or get the state of an IoT actuator."""

import json

try:
    import requests
except ImportError:
    requests = None


def run(actuator_id: str, operation: str, value: str = "") -> str:
    """Control or query an IoT actuator via the gateway.

    @param actuator_id: Unique identifier of the actuator.
    @param operation: 'set' to change the value, 'get' to read current state.
    @param value: Value to set (required for set).
    @returns JSON string with the actuator state.
    @throws ValueError: If the operation is invalid or device_host is missing.
    """
    if operation == "get":
        return _get_actuator(actuator_id)
    if operation == "set":
        return _set_actuator(actuator_id, value)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'set' or 'get'.")


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    import os
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")


def _get_actuator(actuator_id: str) -> str:
    """Get the current state of an actuator."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/actuators/{actuator_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "actuator_id": actuator_id,
        "value": data.get("value"),
        "status": data.get("status", "ok"),
        "last_updated": data.get("last_updated", ""),
    }, indent=2)


def _set_actuator(actuator_id: str, value: str) -> str:
    """Set an actuator to the specified value."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/actuators/{actuator_id}"

    response = requests.post(url, json={"value": value}, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "actuator_id": actuator_id,
        "value": value,
        "status": data.get("status", "ok"),
        "previous_value": data.get("previous_value"),
    }, indent=2)
