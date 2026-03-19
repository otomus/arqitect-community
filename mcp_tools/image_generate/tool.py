"""Generate an image from a text prompt."""

import os


def run(prompt: str, model: str = "") -> str:
    """Generate an image using a configured image API endpoint."""
    api_endpoint = os.environ.get("ARQITECT_IMAGE_API", "")
    if not api_endpoint:
        raise RuntimeError(
            "Image generation requires configuration of an image API endpoint. "
            "Set ARQITECT_IMAGE_API env var."
        )
    # When configured, this would call the API endpoint
    raise NotImplementedError(
        f"Image API configured at {api_endpoint} but generation logic not yet implemented."
    )
