"""Send an HTTP POST request."""

import json
import urllib.request


def run(url: str, body: str, headers: str = "{}") -> str:
    """Send a POST request and return the response body."""
    hdrs = json.loads(headers)
    hdrs.setdefault("Content-Type", "application/json")
    data = body.encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")
