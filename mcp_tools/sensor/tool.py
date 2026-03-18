"""Read a sensor value or list available sensors on the IoT gateway."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(operation: str, sensor_id: str = "", type: str = "", device: str = "") -> str:
    """Read a sensor or list all sensors via the IoT gateway.

    @param operation: 'read' to get a sensor value, 'list' to enumerate sensors.
    @param sensor_id: Sensor identifier (required for read).
    @param type: Filter by sensor type (optional, list only).
    @param device: Filter by parent device (optional, list only).
    @returns JSON string with sensor data.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "read":
        return _read_sensor(sensor_id)
    if operation == "list":
        return _list_sensors(type, device)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'list'.")


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")


def _read_sensor(sensor_id: str) -> str:
    """Read the current value from a sensor."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
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


def _list_sensors(sensor_type: str, device_filter: str) -> str:
    """List all sensors registered on the IoT gateway."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/sensors"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    sensors = data if isinstance(data, list) else data.get("sensors", [])

    if sensor_type:
        sensors = [s for s in sensors if s.get("type") == sensor_type]
    if device_filter:
        sensors = [s for s in sensors if s.get("device") == device_filter]

    return json.dumps({
        "host": host,
        "count": len(sensors),
        "sensors": sensors,
    }, indent=2)
