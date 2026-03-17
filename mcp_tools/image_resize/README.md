# image_resize

Resize an image to the specified width and height using Pillow.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source image file |
| output_path | string | yes | Path where the resized image will be saved |
| width | number | yes | Target width in pixels |
| height | number | yes | Target height in pixels |

## Usage

```python
result = run("photo.jpg", "photo_small.jpg", 200, 150)
```
