"""Control a smart speaker: play, pause, or adjust volume."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(device_id: str, operation: str, uri: str = "", level: str = "") -> str:
    """Control a smart speaker via the IoT gateway.

    @param device_id: Unique identifier of the speaker.
    @param operation: 'play' to start playback, 'pause' to stop, 'volume' to adjust.
    @param uri: Media URI to play (play only).
    @param level: Volume level 0-100 (volume only).
    @returns JSON string confirming the action.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "play":
        return _play(device_id, uri)
    if operation == "pause":
        return _pause(device_id)
    if operation == "volume":
        return _volume(device_id, level)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'play', 'pause', or 'volume'.")


def _get_host() -> str:
    """Retrieve the IoT gateway host from environment or use default."""
    return os.environ.get("IOT_GATEWAY_HOST", "http://localhost:8080").rstrip("/")


def _play(device_id: str, uri: str) -> str:
    """Start media playback on a speaker."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/speakers/{device_id}/play"
    body: dict = {}
    if uri:
        body["uri"] = uri

    response = requests.post(url, json=body, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "action": "play",
        "uri": uri,
        "status": data.get("status", "ok"),
    }, indent=2)


def _pause(device_id: str) -> str:
    """Pause media playback on a speaker."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/speakers/{device_id}/pause"

    response = requests.post(url, json={}, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "action": "pause",
        "status": data.get("status", "ok"),
    }, indent=2)


def _volume(device_id: str, level: str) -> str:
    """Set the volume level on a speaker."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    host = _get_host()
    url = f"{host}/api/v1/speakers/{device_id}/volume"

    response = requests.post(url, json={"level": int(level)}, timeout=10)
    response.raise_for_status()
    data = response.json()

    return json.dumps({
        "device_id": device_id,
        "action": "volume",
        "level": int(level),
        "status": data.get("status", "ok"),
    }, indent=2)
