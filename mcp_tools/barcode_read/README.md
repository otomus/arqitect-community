# barcode_read

Read and decode barcodes from image files. Uses pyzbar with Pillow for decoding.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| image_path | string | yes | Path to the image containing a barcode |

## Usage

```python
result = run(image_path="barcode.png")
# Returns: "[CODE128] ABC-12345"
```
