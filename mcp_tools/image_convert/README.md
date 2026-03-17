# image_convert

Convert an image to a different format (png, jpg, webp, bmp) using Pillow.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source image file |
| output_path | string | yes | Path where the converted image will be saved |
| format | string | yes | Target format: png, jpg, webp, or bmp |

## Usage

```python
result = run("photo.png", "photo.webp", "webp")
```
