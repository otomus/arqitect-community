"""Download a video from a URL using yt-dlp."""

import os


def run(url: str, output_path: str, format: str = "best") -> str:
    """Download a video from the given URL.

    Args:
        url: URL of the video to download.
        output_path: Path where the downloaded video will be saved.
        format: yt-dlp format selector (e.g. 'best', 'mp4', 'bestvideo+bestaudio').

    Returns:
        Confirmation message with the output path, or an error message.
    """
    try:
        import yt_dlp
    except ImportError:
        return "Error: yt-dlp is not installed. Run: pip install yt-dlp"

    if not url:
        return "Error: url is required"

    resolved_output = os.path.abspath(output_path)
    ydl_opts = {
        "format": format,
        "outtmpl": resolved_output,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:
        return f"Error downloading video: {exc}"

    return f"Video downloaded and saved to {resolved_output}"
