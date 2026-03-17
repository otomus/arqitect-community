# qr_code_generate

Generate QR code images from text, URLs, or other data. Uses the qrcode library with PIL.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | string | yes | Data to encode in the QR code |
| output_path | string | yes | Output file path for the image |
| size | integer | no | Box size per QR module (default: 10) |

## Usage

```python
result = run(
    data="https://example.com",
    output_path="qr.png",
    size=15
)
```
