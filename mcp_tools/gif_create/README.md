# gif_create

Create an animated GIF from a list of image files using Pillow.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| image_paths | string | yes | JSON array of image file paths |
| output_path | string | yes | Path where the GIF will be saved |
| duration | number | no | Duration per frame in milliseconds (default: 500) |

## Usage

```python
result = run('["frame1.png", "frame2.png", "frame3.png"]', "animation.gif", 300)
```
