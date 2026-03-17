# stock_history

Get historical stock price data (OHLCV) for a given ticker symbol using yfinance.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| symbol | string | Yes | Stock ticker symbol (e.g. AAPL) |
| period | string | Yes | Time period: 1d, 5d, 1mo, 3mo, or 1y |

## Dependencies

- `yfinance` - Install with `pip install yfinance`

## Usage

```python
result = run("AAPL", "1mo")
```
