# audio_convert

Convert audio to a different format (mp3, wav, ogg, flac) using ffmpeg.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| input_path | string | yes | Path to the source audio file |
| output_path | string | yes | Path where the converted audio will be saved |
| format | string | yes | Target format: mp3, wav, ogg, or flac |

## Usage

```python
result = run("recording.wav", "recording.mp3", "mp3")
```
