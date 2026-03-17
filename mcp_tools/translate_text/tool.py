"""Translate text between languages using a translation API."""

import json
import os

try:
    import requests
except ImportError:
    requests = None


def run(text: str, target_language: str, source_language: str = "auto") -> str:
    """Translate text from one language to another.

    Uses the LibreTranslate-compatible API endpoint configured via
    environment variables.

    @param text: The text to translate.
    @param target_language: ISO 639-1 target language code (e.g. 'es').
    @param source_language: ISO 639-1 source language code, or 'auto' for detection.
    @returns JSON string with translated text and detected source language.
    @throws RuntimeError: If translation fails.
    """
    if requests is None:
        raise ImportError("The 'requests' package is required. Install it with: pip install requests")

    api_key = os.environ.get("TRANSLATE_API_KEY", "")
    if not api_key:
        raise RuntimeError("TRANSLATE_API_KEY environment variable is not set")

    api_url = os.environ.get("TRANSLATE_API_URL", "https://libretranslate.com/translate")

    payload = {
        "q": text,
        "source": source_language,
        "target": target_language,
        "api_key": api_key,
    }

    response = requests.post(api_url, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Translation failed: {data['error']}")

    return json.dumps({
        "source_language": data.get("detectedLanguage", {}).get("language", source_language),
        "target_language": target_language,
        "original": text,
        "translated": data.get("translatedText", ""),
    }, indent=2)
