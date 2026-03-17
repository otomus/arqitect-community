# video_trim

Trim a video to a segment defined by start and end timestamps using ffmpeg.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source video file |
| output_path | string | yes | Path where the trimmed video will be saved |
| start | string | yes | Start time in HH:MM:SS format |
| end | string | yes | End time in HH:MM:SS format |

## Usage

```python
result = run("movie.mp4", "clip.mp4", "00:01:30", "00:03:00")
```
