"""Get stock quotes or historical price data."""

import json

try:
    import yfinance as yf
except ImportError:
    yf = None

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "1y"}


def run(symbol: str, operation: str, period: str = "") -> str:
    """Fetch a stock quote or historical OHLCV data.

    @param symbol: Stock ticker symbol (e.g. AAPL).
    @param operation: 'quote' for current price, 'history' for historical data.
    @param period: Time period for history (1d, 5d, 1mo, 3mo, 1y).
    @returns JSON string with stock data.
    @throws ValueError: If the operation is invalid.
    """
    if operation == "quote":
        return _quote(symbol)
    if operation == "history":
        return _history(symbol, period)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'quote' or 'history'.")


def _quote(symbol: str) -> str:
    """Fetch the latest stock quote."""
    if yf is None:
        return "error: The 'yfinance' package is required. Install it with: pip install yfinance"

    ticker = yf.Ticker(symbol.upper())
    info = ticker.info

    if not info or info.get("regularMarketPrice") is None:
        raise RuntimeError(f"No quote data found for symbol: {symbol}")

    return json.dumps({
        "symbol": symbol.upper(),
        "name": info.get("shortName", ""),
        "price": info.get("regularMarketPrice"),
        "previous_close": info.get("regularMarketPreviousClose"),
        "change": info.get("regularMarketChange"),
        "change_percent": info.get("regularMarketChangePercent"),
        "volume": info.get("regularMarketVolume"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency", "USD"),
    }, indent=2)


def _history(symbol: str, period: str) -> str:
    """Fetch historical OHLCV data for a stock ticker."""
    if yf is None:
        return "error: The 'yfinance' package is required. Install it with: pip install yfinance"

    if not period:
        period = "1mo"

    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period '{period}'. Must be one of: {', '.join(sorted(VALID_PERIODS))}")

    ticker = yf.Ticker(symbol.upper())
    history = ticker.history(period=period)

    if history.empty:
        raise RuntimeError(f"No historical data found for symbol: {symbol}")

    records = []
    for date, row in history.iterrows():
        records.append({
            "date": str(date.date()),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })

    return json.dumps({
        "symbol": symbol.upper(),
        "period": period,
        "data_points": len(records),
        "history": records,
    }, indent=2)
