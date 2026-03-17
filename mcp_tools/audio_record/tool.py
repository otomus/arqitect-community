"""Record audio from the microphone using sounddevice."""

import os

SAMPLE_RATE = 44100
CHANNELS = 1


def run(output_path: str, duration: int) -> str:
    """Record audio from the default microphone and save as WAV.

    Args:
        output_path: Path where the recorded audio will be saved.
        duration: Recording duration in seconds.

    Returns:
        Confirmation message with the output path and duration.
    """
    try:
        import sounddevice as sd
    except ImportError:
        return "Error: sounddevice is not installed. Run: pip install sounddevice"

    try:
        import numpy as np
    except ImportError:
        return "Error: numpy is not installed. Run: pip install numpy"

    try:
        import wave
    except ImportError:
        return "Error: wave module is not available"

    if duration <= 0:
        return "Error: duration must be a positive integer"

    resolved_output = os.path.abspath(output_path)

    try:
        recording = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        )
        sd.wait()
    except Exception as exc:
        return f"Error recording audio: {exc}"

    with wave.open(resolved_output, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit audio = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(recording.tobytes())

    return f"Recorded {duration}s of audio and saved to {resolved_output}"
