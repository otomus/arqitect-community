"""Unified webhook management: send webhook requests and register listeners.

Send uses urllib to POST JSON payloads to webhook URLs.
Listen returns a placeholder response -- an actual listener would require a running server.
"""

import json
import sys
import urllib.request
import urllib.error

VALID_OPERATIONS = {"send", "listen"}


def _handle_send(params: dict) -> dict:
    """Send a webhook POST request with a JSON payload.

    Args:
        params: Must contain 'url'. Optionally 'payload' (JSON string).

    Returns:
        Dict with status, HTTP response code, and response body.

    Raises:
        ValueError: If url is missing.
        RuntimeError: If the HTTP request fails.
    """
    url = params.get("url")
    if not url:
        raise ValueError("url is required for send operation")

    payload_str = params.get("payload", "{}")
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON payload: {e}")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "status": "sent",
                "url": url,
                "http_status": response.status,
                "response": body[:2000],
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"Webhook returned HTTP {e.code}: {body[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to reach webhook URL: {e.reason}")


def _handle_listen(params: dict) -> dict:
    """Register a webhook listener (placeholder).

    A real listener would require starting an HTTP server. This returns
    configuration details that would be needed to set one up.

    Args:
        params: Optionally 'path' and 'events'.

    Returns:
        Dict with listener configuration and a note about limitations.
    """
    path = params.get("path", "/hooks/default")
    events = params.get("events", "")
    event_list = [e.strip() for e in events.split(",") if e.strip()] if events else []

    return {
        "status": "placeholder",
        "note": (
            "Webhook listening requires a running HTTP server. "
            "This tool registered the intent to listen. "
            "Use a persistent server process or a tunneling service (e.g. ngrok) "
            "to expose a local endpoint."
        ),
        "config": {
            "path": path,
            "events": event_list,
        },
    }


HANDLERS = {
    "send": _handle_send,
    "listen": _handle_listen,
}


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        operation = params.get("operation", "")
        if operation not in VALID_OPERATIONS:
            raise ValueError(
                f"Invalid operation: '{operation}'. Must be one of: {', '.join(sorted(VALID_OPERATIONS))}"
            )
        handler = HANDLERS[operation]
        result = handler(params)
        resp = {"id": req.get("id"), "result": json.dumps(result, indent=2)}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
