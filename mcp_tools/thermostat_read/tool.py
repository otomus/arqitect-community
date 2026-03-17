"""Read the current temperature and settings from a smart thermostat."""

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
    """Read the thermostat's current temperature and target settings.

    Calls GET {device_host}/api/v1/thermostats/{device_id} to retrieve
    the current and target temperatures along with the operating mode.

    @param device_id: Unique identifier of the thermostat.
    @param device_host: IoT gateway URL (falls back to SENTIENT_IOT_HOST).
    @returns JSON string with thermostat readings and settings.
    @throws RuntimeError: If the request fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    host = _get_host(device_host)
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
