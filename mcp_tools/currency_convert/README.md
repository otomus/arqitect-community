# currency_convert

Convert an amount between currencies using live exchange rates from exchangerate-api.com.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| amount | float | Yes | Amount to convert |
| from_currency | string | Yes | Source currency code (e.g. USD) |
| to_currency | string | Yes | Target currency code (e.g. EUR) |

## Environment Variables

- `EXCHANGE_RATE_API_KEY` - API key for exchangerate-api.com

## Usage

```python
result = run(100.0, "USD", "EUR")
```
