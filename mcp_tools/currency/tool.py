"""Convert between currencies or get exchange rates."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(from_currency: str, to_currency: str, operation: str, amount: str = "") -> str:
    """Convert an amount or fetch the current exchange rate.

    @param from_currency: ISO 4217 source currency code.
    @param to_currency: ISO 4217 target currency code.
    @param operation: 'convert' to convert an amount, 'rate' to get the exchange rate.
    @param amount: Amount to convert (required for convert).
    @returns JSON string with conversion result or rate.
    @throws ValueError: If the operation is invalid or API key is missing.
    """
    if operation == "convert":
        return _convert(from_currency, to_currency, amount)
    if operation == "rate":
        return _rate(from_currency, to_currency)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'convert' or 'rate'.")


def _get_api_key() -> str:
    """Retrieve the exchange rate API key from environment."""
    key = os.environ.get("EXCHANGE_RATE_API_KEY", "")
    if not key:
        raise ValueError("EXCHANGE_RATE_API_KEY environment variable is required")
    return key


def _convert(from_currency: str, to_currency: str, amount: str) -> str:
    """Convert a monetary amount from one currency to another."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    api_key = _get_api_key()
    src = from_currency.upper()
    tgt = to_currency.upper()
    amt = float(amount)
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{src}/{tgt}/{amt}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise RuntimeError(f"Currency conversion failed: {data.get('error-type', 'unknown error')}")

    return json.dumps({
        "from": src,
        "to": tgt,
        "amount": amt,
        "rate": data["conversion_rate"],
        "converted": data["conversion_result"],
    }, indent=2)


def _rate(from_currency: str, to_currency: str) -> str:
    """Fetch the live exchange rate for a currency pair."""
    if requests is None:
        return "error: The 'requests' package is required. Install it with: pip install requests"

    api_key = _get_api_key()
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
