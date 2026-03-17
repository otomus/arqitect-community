"""Shorten a URL using the is.gd service."""

import json
import urllib.parse
import urllib.request


def run(url: str) -> str:
    """Shorten a URL using the is.gd free service."""
    encoded = urllib.parse.urlencode({"format": "json", "url": url})
    api_url = f"https://is.gd/create.php?{encoded}"
    req = urllib.request.Request(api_url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "shorturl" in data:
        return data["shorturl"]
    raise RuntimeError(f"Shortening failed: {data.get('errormessage', 'unknown error')}")
