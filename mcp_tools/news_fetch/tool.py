"""Fetch news articles matching a search query."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(query: str, count: int = 5) -> str:
    """Fetch news articles from NewsAPI matching the given query.

    @param query: Search keywords for finding relevant articles.
    @param count: Maximum number of articles to return (default 5).
    @returns JSON string with a list of article titles, sources, and URLs.
    @throws RuntimeError: If the API call fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    api_key = os.environ.get("NEWS_API_KEY", "")
    if not api_key:
        raise RuntimeError("NEWS_API_KEY environment variable is not set")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "pageSize": count,
        "sortBy": "publishedAt",
        "apiKey": api_key,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"News fetch failed: {data.get('message', 'unknown error')}")

    articles = [
        {
            "title": article["title"],
            "source": article["source"]["name"],
            "url": article["url"],
            "published_at": article["publishedAt"],
            "description": article.get("description", ""),
        }
        for article in data.get("articles", [])
    ]

    return json.dumps({
        "query": query,
        "total_results": data.get("totalResults", 0),
        "articles": articles,
    }, indent=2)
