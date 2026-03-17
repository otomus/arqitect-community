# image_to_text

Extract text from an image using OCR via pytesseract. Requires Tesseract to be installed on the system.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| image_path | string | yes | Path to the image file |
| language | string | no | Tesseract language code (default: eng) |

## Usage

```python
text = run("screenshot.png")
text = run("document.jpg", language="fra")
```
