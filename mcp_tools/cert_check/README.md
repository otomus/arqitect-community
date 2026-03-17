# cert_check

Check SSL certificate for a domain.

## Usage

```python
result = run("example.com")
# Returns: issuer, expiry, days_remaining, SAN list
```