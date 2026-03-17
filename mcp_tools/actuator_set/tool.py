"""Set the value of an IoT actuator."""

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


def run(actuator_id: str, value: str, device_host: str = "") -> str:
    """Set an actuator to the specified value via the IoT gateway.

    Calls POST {device_host}/api/v1/actuators/{actuator_id} with the
    desired value in the request body.

    @param actuator_id: Unique identifier of the actuator.
    @param value: The value to set.
    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string confirming the actuator state change.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
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
