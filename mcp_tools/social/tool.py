"""Unified social media management: post, read, search, reply, like, followers, and trending.

Supports Twitter and Mastodon platforms via their respective APIs.
Requires the 'requests' package and platform-specific API keys set as env vars:
  SENTIENT_TWITTER_API_KEY, SENTIENT_MASTODON_API_KEY, SENTIENT_MASTODON_INSTANCE
"""

import json
import os
import sys

try:
    import requests
except ImportError:
    requests = None

VALID_OPERATIONS = {"post", "read", "search", "reply", "like", "followers", "trending"}

TWITTER_API_KEY = os.environ.get("SENTIENT_TWITTER_API_KEY", "")
MASTODON_API_KEY = os.environ.get("SENTIENT_MASTODON_API_KEY", "")
MASTODON_INSTANCE = os.environ.get("SENTIENT_MASTODON_INSTANCE", "https://mastodon.social")

REQUEST_TIMEOUT = 10


def _check_requests() -> None:
    """Verify the requests library is available.

    Raises:
        RuntimeError: If requests is not installed.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required. Install it with: pip install requests")


def _get_api_key(platform: str) -> str:
    """Resolve the API key for a given platform.

    Args:
        platform: Platform name (lowercase).

    Returns:
        API key string.

    Raises:
        ValueError: If no API key is configured for the platform.
    """
    if platform == "twitter":
        if not TWITTER_API_KEY:
            raise ValueError("Set SENTIENT_TWITTER_API_KEY environment variable for Twitter access")
        return TWITTER_API_KEY
    if platform == "mastodon":
        if not MASTODON_API_KEY:
            raise ValueError("Set SENTIENT_MASTODON_API_KEY environment variable for Mastodon access")
        return MASTODON_API_KEY
    raise ValueError(f"Unsupported platform: {platform}. Supported: twitter, mastodon")


def _get_instance(platform: str) -> str:
    """Get the instance URL for federated platforms.

    Args:
        platform: Platform name (lowercase).

    Returns:
        Instance URL string.
    """
    if platform == "mastodon":
        return MASTODON_INSTANCE
    return ""


def _region_to_woeid(region: str) -> int:
    """Map common region codes to Twitter WOEIDs.

    Args:
        region: Two-letter country code.

    Returns:
        WOEID integer.
    """
    region_map = {
        "US": 23424977,
        "UK": 23424975,
        "JP": 23424856,
        "DE": 23424829,
        "FR": 23424819,
        "BR": 23424768,
    }
    return region_map.get(region.upper(), 1)


def _handle_post(params: dict) -> dict:
    """Create a new social media post.

    Args:
        params: Must contain 'platform' and 'content'.

    Returns:
        Dict with status and post details.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    content = params.get("content")
    if not content:
        raise ValueError("content is required for post operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json={"text": content},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "posted", "platform": platform, "post_id": data.get("data", {}).get("id", "")}

    if platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.post(
            f"{instance}/api/v1/statuses",
            json={"status": content},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "posted", "platform": platform, "post_id": data.get("id", "")}

    raise ValueError(f"Unsupported platform: {platform}")


def _handle_read(params: dict) -> dict:
    """Read a specific post by ID.

    Args:
        params: Must contain 'platform' and 'post_id'.

    Returns:
        Dict with post content and metadata.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    post_id = params.get("post_id")
    if not post_id:
        raise ValueError("post_id is required for read operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        response = requests.get(
            f"https://api.twitter.com/2/tweets/{post_id}",
            headers=headers,
            params={"tweet.fields": "created_at,author_id,text"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        return {"status": "ok", "platform": platform, "post": data}

    if platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.get(
            f"{instance}/api/v1/statuses/{post_id}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "status": "ok",
            "platform": platform,
            "post": {
                "id": data.get("id"),
                "content": data.get("content"),
                "created_at": data.get("created_at"),
                "account": data.get("account", {}).get("acct", ""),
            },
        }

    raise ValueError(f"Unsupported platform: {platform}")


def _handle_search(params: dict) -> dict:
    """Search for posts matching a query.

    Args:
        params: Must contain 'platform' and 'query'.

    Returns:
        Dict with matching posts.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    query = params.get("query")
    if not query:
        raise ValueError("query is required for search operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=headers,
            params={"query": query, "max_results": 10},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        posts = data.get("data", [])
        return {"status": "ok", "platform": platform, "query": query, "count": len(posts), "posts": posts}

    if platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.get(
            f"{instance}/api/v2/search",
            headers=headers,
            params={"q": query, "type": "statuses", "limit": 10},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        statuses = data.get("statuses", [])
        posts = [{"id": s.get("id"), "content": s.get("content"), "account": s.get("account", {}).get("acct", "")} for s in statuses]
        return {"status": "ok", "platform": platform, "query": query, "count": len(posts), "posts": posts}

    raise ValueError(f"Unsupported platform: {platform}")


def _handle_reply(params: dict) -> dict:
    """Reply to a specific post.

    Args:
        params: Must contain 'platform', 'post_id', and 'content'.

    Returns:
        Dict with status and reply details.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    post_id = params.get("post_id")
    content = params.get("content")
    if not post_id:
        raise ValueError("post_id is required for reply operation")
    if not content:
        raise ValueError("content is required for reply operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json={"text": content, "reply": {"in_reply_to_tweet_id": post_id}},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "replied", "platform": platform, "reply_id": data.get("data", {}).get("id", "")}

    if platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.post(
            f"{instance}/api/v1/statuses",
            json={"status": content, "in_reply_to_id": post_id},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {"status": "replied", "platform": platform, "reply_id": data.get("id", "")}

    raise ValueError(f"Unsupported platform: {platform}")


def _handle_like(params: dict) -> dict:
    """Like/favourite a post.

    Args:
        params: Must contain 'platform' and 'post_id'.

    Returns:
        Dict with status confirming the like.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    post_id = params.get("post_id")
    if not post_id:
        raise ValueError("post_id is required for like operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        response = requests.post(
            "https://api.twitter.com/2/users/me/likes",
            json={"tweet_id": post_id},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    elif platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.post(
            f"{instance}/api/v1/statuses/{post_id}/favourite",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    return {"status": "liked", "platform": platform, "post_id": post_id}


def _handle_followers(params: dict) -> dict:
    """Get follower count and info for a user.

    Args:
        params: Must contain 'platform' and 'user'.

    Returns:
        Dict with follower count and user metadata.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    username = params.get("user")
    if not username:
        raise ValueError("user is required for followers operation")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        response = requests.get(
            url,
            headers=headers,
            params={"user.fields": "public_metrics"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        metrics = data.get("public_metrics", {})
        return {
            "platform": platform,
            "username": username,
            "followers": metrics.get("followers_count", 0),
            "following": metrics.get("following_count", 0),
        }

    if platform == "mastodon":
        instance = _get_instance(platform)
        response = requests.get(
            f"{instance}/api/v1/accounts/lookup",
            params={"acct": username},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "platform": platform,
            "username": username,
            "followers": data.get("followers_count", 0),
            "following": data.get("following_count", 0),
            "display_name": data.get("display_name", ""),
        }

    raise ValueError(f"Unsupported platform: {platform}")


def _handle_trending(params: dict) -> dict:
    """Get trending topics on a platform.

    Args:
        params: Must contain 'platform'. Optionally 'region'.

    Returns:
        Dict with list of trending topics.
    """
    _check_requests()
    platform = params["platform"].lower()
    api_key = _get_api_key(platform)
    region = params.get("region", "")

    headers = {"Authorization": f"Bearer {api_key}"}

    if platform == "twitter":
        woeid = _region_to_woeid(region) if region else 1
        url = f"https://api.twitter.com/1.1/trends/place.json?id={woeid}"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        trends = [
            {"name": t["name"], "tweet_volume": t.get("tweet_volume")}
            for t in data[0].get("trends", [])
        ]
        return {"platform": platform, "region": region or "worldwide", "trends": trends}

    if platform == "mastodon":
        instance = _get_instance(platform)
        url = f"{instance}/api/v1/trends/tags"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        trends = [
            {"name": f"#{t['name']}", "uses": t.get("history", [{}])[0].get("uses", 0)}
            for t in data
        ]
        return {"platform": platform, "region": region or "global", "trends": trends}

    raise ValueError(f"Unsupported platform: {platform}")


HANDLERS = {
    "post": _handle_post,
    "read": _handle_read,
    "search": _handle_search,
    "reply": _handle_reply,
    "like": _handle_like,
    "followers": _handle_followers,
    "trending": _handle_trending,
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
        platform = params.get("platform", "")
        if not platform:
            raise ValueError("platform is required")
        handler = HANDLERS[operation]
        result = handler(params)
        resp = {"id": req.get("id"), "result": json.dumps(result, indent=2)}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
