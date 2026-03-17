"""List all available sensors on the IoT gateway."""

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
    """List all sensors registered on the IoT gateway.

    Calls GET {device_host}/api/v1/sensors to retrieve the full sensor list.

    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string with a list of available sensors.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
    url = f"{host}/api/v1/sensors"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    sensors = data if isinstance(data, list) else data.get("sensors", [])

    return json.dumps({
        "host": host,
        "count": len(sensors),
        "sensors": sensors,
    }, indent=2)
