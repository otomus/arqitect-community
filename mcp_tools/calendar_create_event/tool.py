"""Create a new calendar event using platform-specific APIs."""

import json
import subprocess
import sys
from datetime import datetime


def run(title: str, start: str, end: str, description: str = "") -> str:
    """Create a calendar event on the local system calendar.

    On macOS, creates the event in the default Calendar app via AppleScript.

    @param title: The event title.
    @param start: Start datetime in ISO format.
    @param end: End datetime in ISO format.
    @param description: Optional event description.
    @returns JSON string confirming event creation.
    @throws RuntimeError: If event creation fails.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    if end_dt <= start_dt:
        raise ValueError("End time must be after start time")

    if sys.platform != "darwin":
        return json.dumps({
            "status": "unsupported",
            "note": "Calendar event creation is currently supported only on macOS.",
            "event": {"title": title, "start": start, "end": end},
        }, indent=2)

    start_str = start_dt.strftime("%m/%d/%Y %I:%M:%S %p")
    end_str = end_dt.strftime("%m/%d/%Y %I:%M:%S %p")
    desc_line = f'set description of newEvent to "{description}"' if description else ""

    script = f'''
    tell application "Calendar"
        tell calendar 1
            set newEvent to make new event with properties {{summary:"{title}", start date:date "{start_str}", end date:date "{end_str}"}}
            {desc_line}
        end tell
    end tell
    return "ok"
    '''

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create event: {result.stderr.strip()}")

    return json.dumps({
        "status": "created",
        "event": {
            "title": title,
            "start": start,
            "end": end,
            "description": description,
        },
    }, indent=2)
