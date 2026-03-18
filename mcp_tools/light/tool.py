"""Set or get the state of a smart light via the IoT gateway."""

import json

try:
    import requests
except ImportError:
    requests = None


def run(light_id: str, operation: str, brightness: str = "", color: str = "", on: str = "") -> str:
    """Control or query a smart light.

    @param light_id: Unique identifier of the light.
    @param operation: 'set' to change the light state, 'get' to read it.
    @param brightness: Brightness level 0-100 (set only).
    @param color: Color value (set only).
    @param on: Power state 'true' or 'false' (set only).
    @returns JSON string with the light state.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "get":
        return _get_light(light_id)
    if operation == "set":
        return _set_light(light_id, brightness, color, on)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'set' or 'get'.")


def _get_light(light_id: str) -> str:
    """Get the current state of a light from the IoT gateway."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    device_host = _get_host()
    url = f"{device_host}/api/v1/lights/{light_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "light_id": light_id,
        "on": data.get("on", False),
        "brightness": data.get("brightness"),
        "color": data.get("color", ""),
        "status": data.get("status", "ok"),
    }, indent=2)


def _set_light(light_id: str, brightness: str, color: str, on: str) -> str:
    """Set the state of a light via the IoT gateway."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    device_host = _get_host()
    url = f"{device_host}/api/v1/lights/{light_id}"

    body: dict = {}
    if brightness:
        body["brightness"] = int(brightness)
    if color:
        body["color"] = color
    if on:
        body["on"] = on.lower() == "true"

    response = requests.post(url, json=body, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "light_id": light_id,
        "on": data.get("on"),
        "brightness": data.get("brightness"),
        "color": data.get("color"),
        "status": data.get("status", "ok"),
    }, indent=2)


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    import os
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")
