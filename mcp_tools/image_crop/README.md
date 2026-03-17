# image_crop

Crop an image to the specified bounding box using Pillow.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source image file |
| output_path | string | yes | Path where the cropped image will be saved |
| left | number | yes | Left edge of the crop box in pixels |
| top | number | yes | Top edge of the crop box in pixels |
| right | number | yes | Right edge of the crop box in pixels |
| bottom | number | yes | Bottom edge of the crop box in pixels |

## Usage

```python
result = run("photo.jpg", "photo_cropped.jpg", 10, 10, 200, 150)
```
