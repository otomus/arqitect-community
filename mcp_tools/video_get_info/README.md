# video_get_info

Get video metadata (duration, resolution, codecs, bitrate, etc.) using ffprobe.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the video file |

## Usage

```python
info = run("movie.mp4")
# Returns JSON with duration, resolution, codec info, and stream details
```
