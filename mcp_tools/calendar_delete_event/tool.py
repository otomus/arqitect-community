"""Delete a calendar event by its identifier."""

import json
import subprocess
import sys


def run(event_id: str) -> str:
    """Delete a calendar event from the local system calendar.

    On macOS, removes the event from the Calendar app via AppleScript
    by matching the event summary (used as the identifier).

    @param event_id: The event identifier (title/summary on macOS).
    @returns JSON string confirming deletion.
    @throws RuntimeError: If deletion fails or event is not found.
    """
    if sys.platform != "darwin":
        return json.dumps({
            "status": "unsupported",
            "note": "Calendar event deletion is currently supported only on macOS.",
            "event_id": event_id,
        }, indent=2)

    script = f'''
    tell application "Calendar"
        repeat with cal in calendars
            set evts to (every event of cal whose summary is "{event_id}")
            repeat with evt in evts
                delete evt
                return "deleted"
            end repeat
        end repeat
        return "not_found"
    end tell
    '''

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to delete event: {result.stderr.strip()}")

    output = result.stdout.strip()

    if output == "not_found":
        raise RuntimeError(f"Event not found: {event_id}")

    return json.dumps({
        "status": "deleted",
        "event_id": event_id,
    }, indent=2)
