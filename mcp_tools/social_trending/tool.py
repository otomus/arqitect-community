"""Get trending topics on a social media platform."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(platform: str, region: str = "") -> str:
    """Fetch currently trending topics from the specified platform.

    @param platform: Name of the social media platform.
    @param region: Optional region/country code for localized trends.
    @returns JSON string with a list of trending topics.
    @throws RuntimeError: If the API call fails or platform is unsupported.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    platform_lower = platform.lower()
    env_key = f"{platform.upper()}_API_KEY"
    api_key = os.environ.get(env_key, "")

    if not api_key:
        raise RuntimeError(f"{env_key} environment variable is not set")

    if platform_lower == "twitter":
        # Twitter v2 does not have a direct trends endpoint for free tier;
        # using the v1.1 trends/place endpoint with WOEID.
        woeid = _region_to_woeid(region) if region else 1  # 1 = worldwide
        url = f"https://api.twitter.com/1.1/trends/place.json?id={woeid}"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        trends = [
            {"name": t["name"], "tweet_volume": t.get("tweet_volume")}
            for t in data[0].get("trends", [])
        ]
        return json.dumps({
            "platform": platform_lower,
            "region": region or "worldwide",
            "trends": trends,
        }, indent=2)

    if platform_lower == "mastodon":
        instance = os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
        url = f"{instance}/api/v1/trends/tags"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        trends = [{"name": f"#{t['name']}", "uses": t.get("history", [{}])[0].get("uses", 0)} for t in data]
        return json.dumps({
            "platform": platform_lower,
            "region": region or "global",
            "trends": trends,
        }, indent=2)

    raise RuntimeError(f"Unsupported platform: {platform}. Supported: twitter, mastodon")


def _region_to_woeid(region: str) -> int:
    """Map common region codes to Twitter WOEIDs."""
    region_map = {
        "US": 23424977,
        "UK": 23424975,
        "JP": 23424856,
        "DE": 23424829,
        "FR": 23424819,
        "BR": 23424768,
    }
    return region_map.get(region.upper(), 1)
