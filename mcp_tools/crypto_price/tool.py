"""Get the current price of a cryptocurrency."""

import json
import urllib.parse
import urllib.request


def run(symbol: str) -> str:
    """Fetch the current USD price from CoinGecko free API."""
    coin_id = urllib.parse.quote(symbol.lower().strip())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if coin_id not in data:
        raise ValueError(
            f"Unknown cryptocurrency '{symbol}'. Use CoinGecko IDs like "
            "'bitcoin', 'ethereum', 'dogecoin'."
        )

    return json.dumps(data[coin_id], indent=2)
