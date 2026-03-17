# video_extract_frames

Extract frames from a video at a specified frame rate using ffmpeg. Frames are saved as numbered PNG files.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source video file |
| output_dir | string | yes | Directory where extracted frames will be saved |
| fps | number | no | Frames per second to extract (default: 1) |

## Usage

```python
result = run("video.mp4", "./frames/", 2.0)
```
