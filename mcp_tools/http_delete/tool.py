"""Send an HTTP DELETE request."""

import json
import urllib.request


def run(url: str, headers: str = "{}") -> str:
    """Send a DELETE request and return the response body."""
    hdrs = json.loads(headers)
    req = urllib.request.Request(url, headers=hdrs, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")
