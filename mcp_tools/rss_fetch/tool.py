"""Fetch and parse an RSS or Atom feed."""

import json
import urllib.request
import xml.etree.ElementTree as ET


def _text(element: ET.Element | None) -> str:
    """Safely extract text from an XML element."""
    if element is None:
        return ""
    return (element.text or "").strip()


def run(url: str) -> str:
    """Fetch an RSS/Atom feed and return entries as JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    root = ET.fromstring(raw)
    entries = []

    # Handle Atom feeds (namespace-aware)
    atom_ns = "{http://www.w3.org/2005/Atom}"
    atom_entries = root.findall(f"{atom_ns}entry")
    if atom_entries:
        for entry in atom_entries:
            link_el = entry.find(f"{atom_ns}link")
            link = link_el.get("href", "") if link_el is not None else ""
            entries.append({
                "title": _text(entry.find(f"{atom_ns}title")),
                "link": link,
                "summary": _text(entry.find(f"{atom_ns}summary")),
                "published": _text(entry.find(f"{atom_ns}published"))
                or _text(entry.find(f"{atom_ns}updated")),
            })
        return json.dumps(entries, indent=2)

    # Handle RSS 2.0 feeds
    for item in root.iter("item"):
        entries.append({
            "title": _text(item.find("title")),
            "link": _text(item.find("link")),
            "summary": _text(item.find("description")),
            "published": _text(item.find("pubDate")),
        })

    return json.dumps(entries, indent=2)
