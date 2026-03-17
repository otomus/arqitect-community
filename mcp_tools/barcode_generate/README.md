# barcode_generate

Generate barcode images in Code128, EAN-13, or UPC-A format. Uses the python-barcode library with Pillow.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| data | string | yes | Data to encode in the barcode |
| barcode_type | string | no | code128, ean13, or upc (default: code128) |
| output_path | string | yes | Output file path for the image |

## Usage

```python
result = run(
    data="ABC-12345",
    output_path="barcode.png",
    barcode_type="code128"
)
```
