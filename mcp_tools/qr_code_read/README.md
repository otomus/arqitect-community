# qr_code_read

Read and decode QR codes from image files. Supports pyzbar (with Pillow) or OpenCV as backends.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| image_path | string | yes | Path to the image containing a QR code |

## Usage

```python
result = run(image_path="qr.png")
# Returns the decoded text/URL from the QR code
```
