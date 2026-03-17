"""Read the current value from an IoT sensor."""

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


def run(sensor_id: str, device_host: str = "") -> str:
    """Read the current value from a sensor via the IoT gateway REST API.

    Calls GET {device_host}/api/v1/sensors/{sensor_id} to retrieve
    the latest reading.

    @param sensor_id: Unique identifier of the sensor.
    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string with the sensor reading.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
    url = f"{host}/api/v1/sensors/{sensor_id}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "sensor_id": sensor_id,
        "value": data.get("value"),
        "unit": data.get("unit", ""),
        "timestamp": data.get("timestamp", ""),
        "status": data.get("status", "ok"),
    }, indent=2)
