# stock_quote

Get the current stock quote for a given ticker symbol using yfinance.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| symbol | string | Yes | Stock ticker symbol (e.g. AAPL, MSFT) |

## Dependencies

- `yfinance` - Install with `pip install yfinance`

## Usage

```python
result = run("AAPL")
```
