"""Identify a song from an audio sample."""


def run(audio_path: str) -> str:
    """Identify music from an audio file."""
    raise RuntimeError(
        "Music identification requires Shazam API configuration. "
        "Set ARQITECT_SHAZAM_API_KEY env var."
    )
