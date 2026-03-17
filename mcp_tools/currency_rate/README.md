# currency_rate

Get the current exchange rate between two currencies.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| from_currency | string | Yes | Source currency code (e.g. USD) |
| to_currency | string | Yes | Target currency code (e.g. EUR) |

## Environment Variables

- `EXCHANGE_RATE_API_KEY` - API key for exchangerate-api.com

## Usage

```python
result = run("USD", "EUR")
```
