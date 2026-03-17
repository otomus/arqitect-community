# audio_record

Record audio from the default microphone for a specified duration. Saves output as WAV.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| output_path | string | yes | Path where the recorded audio will be saved |
| duration | number | yes | Recording duration in seconds |

## Usage

```python
result = run("recording.wav", 10)
```
