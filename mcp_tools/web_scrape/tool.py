"""Fetch a web page and extract text content."""

import re
import urllib.request
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    """Simple HTML parser that extracts visible text."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


def _extract_by_selector(html: str, selector: str) -> str:
    """Extract text from elements matching a basic CSS selector (tag, .class, #id)."""
    if selector.startswith("#"):
        # ID selector
        pattern = rf'<[^>]+id="{re.escape(selector[1:])}"[^>]*>(.*?)</[^>]+>'
    elif selector.startswith("."):
        # Class selector
        cls = re.escape(selector[1:])
        pattern = rf'<[^>]+class="[^"]*\b{cls}\b[^"]*"[^>]*>(.*?)</[^>]+>'
    else:
        # Tag selector
        tag = re.escape(selector)
        pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"

    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    parts = []
    for match in matches:
        clean = re.sub(r"<[^>]+>", "", match).strip()
        if clean:
            parts.append(clean)
    return "\n".join(parts)


def run(url: str, selector: str = "") -> str:
    """Fetch a web page and return extracted text."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    if selector:
        return _extract_by_selector(html, selector)

    extractor = _TextExtractor()
    extractor.feed(html)
    return "\n".join(extractor.text_parts)
