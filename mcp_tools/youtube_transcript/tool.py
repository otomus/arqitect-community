"""Download the transcript of a YouTube video."""

import glob
import os
import shutil
import subprocess
import tempfile


def run(video_id: str) -> str:
    """Fetch auto-generated or manual subtitles for a YouTube video."""
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise RuntimeError(
            "yt-dlp not found. Install it with: pip install yt-dlp"
        )

    url = f"https://www.youtube.com/watch?v={video_id}"
    work_dir = tempfile.mkdtemp()

    try:
        subprocess.run(
            [
                yt_dlp,
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en",
                "--sub-format", "vtt",
                "--skip-download",
                "-o", os.path.join(work_dir, "%(id)s.%(ext)s"),
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Find the subtitle file
        vtt_files = glob.glob(os.path.join(work_dir, "*.vtt"))
        if not vtt_files:
            raise RuntimeError("No subtitles found for this video.")

        with open(vtt_files[0], "r", encoding="utf-8") as f:
            content = f.read()

        # Strip VTT headers and timestamps, return plain text
        lines = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if "-->" in line:
                continue
            # Skip numeric cue identifiers
            if line.isdigit():
                continue
            if line not in lines:  # basic dedup for repeated lines
                lines.append(line)

        return "\n".join(lines)
    finally:
        # Clean up temp directory
        for f in glob.glob(os.path.join(work_dir, "*")):
            os.unlink(f)
        os.rmdir(work_dir)
