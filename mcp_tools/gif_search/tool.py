"""Search for GIFs using Tenor API."""

import json
import os
import urllib.parse
import urllib.request


def run(query: str) -> str:
    """Search for GIFs and return results as JSON."""
    api_key = os.environ.get("TENOR_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GIF search requires a Tenor API key. "
            "Set TENOR_API_KEY env var (free at https://developers.google.com/tenor)."
        )

    encoded_query = urllib.parse.quote_plus(query)
    url = (
        f"https://tenor.googleapis.com/v2/search"
        f"?q={encoded_query}&key={api_key}&limit=10"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = []
    for item in data.get("results", []):
        media = item.get("media_formats", {})
        gif_url = media.get("gif", {}).get("url", "")
        results.append({
            "title": item.get("title", ""),
            "url": gif_url,
            "preview": media.get("tinygif", {}).get("url", ""),
        })

    return json.dumps(results, indent=2)
