"""List calendar events for a given date range using platform-specific APIs."""

import json
import subprocess
import sys
from datetime import datetime, timedelta


def _fetch_macos_events(start_date: str, end_date: str) -> list:
    """Fetch events from macOS Calendar using AppleScript."""
    script = f'''
    set startDate to date "{start_date}"
    set endDate to date "{end_date}"
    set output to ""
    tell application "Calendar"
        repeat with cal in calendars
            set evts to (every event of cal whose start date >= startDate and start date <= endDate)
            repeat with evt in evts
                set output to output & summary of evt & "|||" & (start date of evt as string) & "|||" & (end date of evt as string) & "\\n"
            end repeat
        end repeat
    end tell
    return output
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        events = []
        for line in result.stdout.strip().split("\n"):
            if "|||" in line:
                parts = line.split("|||")
                if len(parts) >= 3:
                    events.append({
                        "title": parts[0].strip(),
                        "start": parts[1].strip(),
                        "end": parts[2].strip(),
                    })
        return events
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def run(date: str = "", days: int = 7) -> str:
    """List upcoming calendar events.

    On macOS, reads from the native Calendar app via AppleScript.
    On other platforms, returns an informational message about setup.

    @param date: Start date in ISO format (defaults to today).
    @param days: Number of days to look ahead (default 7).
    @returns JSON string with a list of calendar events.
    """
    if not date:
        start = datetime.now()
    else:
        start = datetime.fromisoformat(date)

    end = start + timedelta(days=days)
    start_str = start.strftime("%m/%d/%Y")
    end_str = end.strftime("%m/%d/%Y")

    if sys.platform == "darwin":
        events = _fetch_macos_events(start_str, end_str)
    else:
        return json.dumps({
            "note": "Calendar integration requires platform-specific setup. macOS uses native Calendar app.",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "events": [],
        }, indent=2)

    return json.dumps({
        "start": start.isoformat(),
        "end": end.isoformat(),
        "count": len(events),
        "events": events,
    }, indent=2)
