"""Browser Close tool — closes a browser page and removes it from the registry."""

import json
import os
import sys

from playwright.sync_api import sync_playwright

_CDP_FILE = os.path.expanduser("~/.arqitect_browser_cdp.json")
_PAGES_FILE = os.path.expanduser("~/.arqitect_browser_pages.json")


def _get_page(page_id: str):
    """Connect to the shared browser via CDP and retrieve a page by its ID.

    Returns:
        Tuple of (playwright instance, browser, page).

    Raises:
        RuntimeError: If no browser is running.
        ValueError: If the page_id is unknown or the page cannot be found.
    """
    if not os.path.exists(_CDP_FILE):
        raise RuntimeError("No browser running. Call browser_open first.")

    with open(_CDP_FILE) as f:
        cdp_info = json.load(f)

    with open(_PAGES_FILE) as f:
        pages_info = json.load(f)

    if page_id not in pages_info:
        raise ValueError(f"No page found for page_id '{page_id}'")

    page_meta = pages_info[page_id]

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(cdp_info["ws_endpoint"])

    for context in browser.contexts:
        for page in context.pages:
            if page.url == page_meta["url"]:
                return pw, browser, page

    raise ValueError(f"Page with URL '{page_meta['url']}' not found in browser")


def _remove_page_mapping(page_id: str):
    """Remove a page_id entry from the shared pages JSON file."""
    if not os.path.exists(_PAGES_FILE):
        return

    with open(_PAGES_FILE) as f:
        pages_info = json.load(f)

    pages_info.pop(page_id, None)

    with open(_PAGES_FILE, "w") as f:
        json.dump(pages_info, f)


def handle_request(params: dict) -> dict:
    """
    Close the page identified by *page_id* and remove it from the registry.

    Args:
        params: Must contain ``page_id`` (str).

    Returns:
        Dict confirming the page was closed.
    """
    page_id = params.get("page_id")

    if not page_id:
        raise ValueError("'page_id' parameter is required")

    pw, browser, page = _get_page(page_id)
    try:
        page.close()
        _remove_page_mapping(page_id)
        return {"closed": page_id}
    finally:
        browser.close()
        pw.stop()


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
