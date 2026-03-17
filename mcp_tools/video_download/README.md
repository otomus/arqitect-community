# video_download

Download a video from a URL using yt-dlp. Supports YouTube, Vimeo, and many other sites.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| url | string | yes | URL of the video to download |
| output_path | string | yes | Path where the downloaded video will be saved |
| format | string | no | yt-dlp format selector (default: best) |

## Usage

```python
result = run("https://www.youtube.com/watch?v=example", "video.mp4")
result = run("https://vimeo.com/123456", "video.mp4", "bestvideo+bestaudio")
```
