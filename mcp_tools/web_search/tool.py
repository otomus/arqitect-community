"""Search the web using DuckDuckGo HTML search."""

import json
import re
import urllib.parse
import urllib.request


def run(query: str, engine: str = "duckduckgo") -> str:
    """Search DuckDuckGo and return top 10 results as JSON."""
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    results = []
    # DuckDuckGo HTML results are in <a class="result__a"> tags
    blocks = re.findall(
        r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )
    for href, title_html, snippet_html in blocks[:10]:
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        snippet = re.sub(r"<[^>]+>", "", snippet_html).strip()
        # DuckDuckGo wraps URLs in a redirect; extract the actual URL
        url_match = re.search(r"uddg=([^&]+)", href)
        actual_url = urllib.parse.unquote(url_match.group(1)) if url_match else href
        results.append({"title": title, "url": actual_url, "snippet": snippet})

    return json.dumps(results, indent=2)
