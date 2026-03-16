import logging
import requests

logger = logging.getLogger(__name__)

VOICE_RECOGNITION_API_URL = "https://api.example.com/voice_recognition"
REQUEST_TIMEOUT_SECONDS = 10


def run(query: str) -> str:
    """
    Sends an audio query to the voice recognition API and returns the transcribed result.
    """
    try:
        response = requests.get(
            VOICE_RECOGNITION_API_URL,
            params={"query": query},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()['result']
    except requests.RequestException as e:
        logger.error("Voice recognition request failed: %s", e)
        return f"Error: {e}"
