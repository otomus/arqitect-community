"""Convert an amount between currencies using live exchange rates."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert a monetary amount from one currency to another.

    Fetches the current exchange rate from exchangerate-api.com and
    returns the converted amount along with the rate used.

    @param amount: The amount to convert.
    @param from_currency: ISO 4217 source currency code (e.g. 'USD').
    @param to_currency: ISO 4217 target currency code (e.g. 'EUR').
    @returns JSON string with the conversion result.
    @throws RuntimeError: If the API call fails or the currency is unsupported.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY", "")
    if not api_key:
        raise RuntimeError("EXCHANGE_RATE_API_KEY environment variable is not set")

    src = from_currency.upper()
    tgt = to_currency.upper()
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{src}/{tgt}/{amount}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise RuntimeError(f"Currency conversion failed: {data.get('error-type', 'unknown error')}")

    return json.dumps({
        "from": src,
        "to": tgt,
        "amount": amount,
        "rate": data["conversion_rate"],
        "converted": data["conversion_result"],
    }, indent=2)
