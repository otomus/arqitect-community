"""Browser Open tool — launches a headless browser and navigates to a URL."""

import json
import os
import sys
import uuid

from playwright.sync_api import sync_playwright

_CDP_FILE = os.path.expanduser("~/.sentient_browser_cdp.json")
_PAGES_FILE = os.path.expanduser("~/.sentient_browser_pages.json")

# ---------------------------------------------------------------------------
# Global state: single browser instance shared across calls within this
# long-lived process.  The CDP endpoint is persisted to disk so that other
# tool subprocesses can reconnect to the same browser.
# ---------------------------------------------------------------------------
_playwright = None
_browser = None


def _ensure_browser():
    """Lazily start Playwright and launch a headless Chromium browser.

    If a CDP endpoint file already exists and the browser is still reachable,
    reconnect to it.  Otherwise launch a fresh browser and persist its CDP
    websocket endpoint to ``~/.sentient_browser_cdp.json``.
    """
    global _playwright, _browser

    if _browser is not None:
        return _browser

    _playwright = sync_playwright().start()

    # Try to reconnect to an existing browser first
    if os.path.exists(_CDP_FILE):
        try:
            with open(_CDP_FILE) as f:
                cdp_info = json.load(f)
            _browser = _playwright.chromium.connect_over_cdp(cdp_info["ws_endpoint"])
            return _browser
        except Exception:
            # Browser is gone — launch a new one
            pass

    _browser = _playwright.chromium.launch(headless=True)

    # Persist the CDP websocket endpoint so other tools can connect
    ws_endpoint = _browser._impl_obj._browser.ws_endpoint
    with open(_CDP_FILE, "w") as f:
        json.dump({"ws_endpoint": ws_endpoint}, f)

    return _browser


def _save_page_mapping(page_id: str, url: str):
    """Persist page_id -> URL mapping to the shared pages JSON file."""
    pages_info: dict = {}
    if os.path.exists(_PAGES_FILE):
        with open(_PAGES_FILE) as f:
            pages_info = json.load(f)

    pages_info[page_id] = {"url": url}

    with open(_PAGES_FILE, "w") as f:
        json.dump(pages_info, f)


def handle_request(params: dict) -> dict:
    """
    Open a new page, navigate to *url*, optionally wait for a CSS selector.

    Args:
        params: Must contain ``url`` (str). May contain ``wait`` (str).

    Returns:
        Dict with ``page_id`` — a UUID identifying the opened page.
    """
    url = params.get("url")
    if not url:
        raise ValueError("'url' parameter is required")

    wait_selector = params.get("wait")

    browser = _ensure_browser()
    page = browser.new_page()
    page.goto(url)

    if wait_selector:
        page.wait_for_selector(wait_selector)

    page_id = str(uuid.uuid4())

    # Persist the mapping so other subprocess tools can find this page
    _save_page_mapping(page_id, page.url)

    return {"page_id": page_id}


# -- stdio JSON-RPC loop ----------------------------------------------------
sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        result = handle_request(params)
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
