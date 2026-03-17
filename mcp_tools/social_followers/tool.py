"""Get follower count and list for a social media user."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(platform: str, username: str) -> str:
    """Fetch the follower count for a user on the specified platform.

    @param platform: Name of the social media platform.
    @param username: The username to look up.
    @returns JSON string with follower count and user info.
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
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"user.fields": "public_metrics"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", {})
        metrics = data.get("public_metrics", {})
        return json.dumps({
            "platform": platform_lower,
            "username": username,
            "followers": metrics.get("followers_count", 0),
            "following": metrics.get("following_count", 0),
        }, indent=2)

    if platform_lower == "mastodon":
        instance = os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
        lookup_url = f"{instance}/api/v1/accounts/lookup"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(lookup_url, params={"acct": username}, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return json.dumps({
            "platform": platform_lower,
            "username": username,
            "followers": data.get("followers_count", 0),
            "following": data.get("following_count", 0),
            "display_name": data.get("display_name", ""),
        }, indent=2)

    raise RuntimeError(f"Unsupported platform: {platform}. Supported: twitter, mastodon")
