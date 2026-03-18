"""Browser Screenshot tool — captures a screenshot of an open browser page."""

import json
import os
import sys
import tempfile

from playwright.sync_api import sync_playwright

_CDP_FILE = os.path.expanduser("~/.sentient_browser_cdp.json")
_PAGES_FILE = os.path.expanduser("~/.sentient_browser_pages.json")


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


def handle_request(params: dict) -> dict:
    """
    Take a screenshot of the page and save it to *path* or a temp file.

    Args:
        params: Must contain ``page_id`` (str). May contain ``path`` (str).

    Returns:
        Dict with ``path`` — the absolute path to the saved screenshot.
    """
    page_id = params.get("page_id")
    output_path = params.get("path")

    if not page_id:
        raise ValueError("'page_id' parameter is required")

    pw, browser, page = _get_page(page_id)
    try:
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            output_path = tmp.name
            tmp.close()

        page.screenshot(path=output_path)
        return {"path": output_path}
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
