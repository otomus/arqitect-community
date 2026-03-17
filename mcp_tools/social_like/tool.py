"""Like a social media post on a specified platform."""

import json
import os

try:
    import requests
except ImportError:
    requests = None

PLATFORM_ENDPOINTS = {
    "twitter": "https://api.twitter.com/2/users/{user_id}/likes",
    "mastodon": "{instance}/api/v1/statuses/{post_id}/favourite",
}


def run(platform: str, post_id: str) -> str:
    """Like a post on the specified social media platform.

    Reads the API key from the environment variable named
    {PLATFORM}_API_KEY (uppercased), e.g. TWITTER_API_KEY.

    @param platform: Name of the social media platform.
    @param post_id: Unique identifier of the post to like.
    @returns JSON string confirming the like action.
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
        url = "https://api.twitter.com/2/tweets"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(
            f"https://api.twitter.com/2/users/me/likes",
            json={"tweet_id": post_id},
            headers=headers,
            timeout=10,
        )
    elif platform_lower == "mastodon":
        instance = os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
        url = f"{instance}/api/v1/statuses/{post_id}/favourite"
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(url, headers=headers, timeout=10)
    else:
        raise RuntimeError(f"Unsupported platform: {platform}. Supported: twitter, mastodon")

    response.raise_for_status()

    return json.dumps({
        "status": "liked",
        "platform": platform_lower,
        "post_id": post_id,
    }, indent=2)
