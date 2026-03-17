"""Get detailed information about a YouTube video using yt-dlp."""

import json
import subprocess


def run(video_id: str) -> str:
    """Fetch metadata for a YouTube video using yt-dlp.

    Does not download the video -- only extracts metadata such as
    title, duration, view count, and description.

    @param video_id: The YouTube video ID.
    @returns JSON string with video metadata.
    @throws RuntimeError: If yt-dlp is not installed or extraction fails.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError("yt-dlp is not installed. Install it with: pip install yt-dlp")

    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch video info: {result.stderr.strip()}")

    data = json.loads(result.stdout)

    return json.dumps({
        "video_id": video_id,
        "title": data.get("title", ""),
        "channel": data.get("channel", ""),
        "duration_seconds": data.get("duration"),
        "view_count": data.get("view_count"),
        "like_count": data.get("like_count"),
        "upload_date": data.get("upload_date", ""),
        "description": (data.get("description", "") or "")[:500],
        "url": url,
    }, indent=2)
