# translate_text

Translate text between languages using a LibreTranslate-compatible API.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| text | string | Yes | Text to translate |
| target_language | string | Yes | Target language code (e.g. es, fr) |
| source_language | string | No | Source language code (auto-detected if omitted) |

## Environment Variables

- `TRANSLATE_API_KEY` - API key for the translation service
- `TRANSLATE_API_URL` - API endpoint (defaults to libretranslate.com)

## Usage

```python
result = run("Hello world", "es")
```
