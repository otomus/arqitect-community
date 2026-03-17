"""Get the current exchange rate between two currencies."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(from_currency: str, to_currency: str) -> str:
    """Fetch the live exchange rate for a currency pair.

    @param from_currency: ISO 4217 source currency code.
    @param to_currency: ISO 4217 target currency code.
    @returns JSON string containing the exchange rate.
    @throws RuntimeError: If the API call fails or currency is unsupported.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY", "")
    if not api_key:
        raise RuntimeError("EXCHANGE_RATE_API_KEY environment variable is not set")

    src = from_currency.upper()
    tgt = to_currency.upper()
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{src}/{tgt}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise RuntimeError(f"Rate lookup failed: {data.get('error-type', 'unknown error')}")

    return json.dumps({
        "from": src,
        "to": tgt,
        "rate": data["conversion_rate"],
        "last_updated": data.get("time_last_update_utc", "unknown"),
    }, indent=2)
