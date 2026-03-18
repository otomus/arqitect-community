"""Unified calendar management: list, create, and delete calendar events.

On macOS, interacts with the native Calendar app via AppleScript.
On other platforms, returns informational messages about setup requirements.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta

VALID_OPERATIONS = {"list", "create", "delete"}


def _fetch_macos_events(start_date: str, end_date: str) -> list:
    """Fetch events from macOS Calendar using AppleScript.

    Args:
        start_date: Start date in MM/DD/YYYY format.
        end_date: End date in MM/DD/YYYY format.

    Returns:
        List of event dictionaries with title, start, and end.
    """
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


def _handle_list(params: dict) -> dict:
    """List calendar events for a given date range.

    Args:
        params: Optionally contains 'start' (ISO date) and 'date_range' (days ahead).

    Returns:
        Dict with event list and metadata.
    """
    start_str = params.get("start", "")
    days = int(params.get("date_range", "7"))

    if not start_str:
        start = datetime.now()
    else:
        start = datetime.fromisoformat(start_str)

    end = start + timedelta(days=days)
    start_fmt = start.strftime("%m/%d/%Y")
    end_fmt = end.strftime("%m/%d/%Y")

    if sys.platform == "darwin":
        events = _fetch_macos_events(start_fmt, end_fmt)
    else:
        return {
            "note": "Calendar integration requires platform-specific setup. macOS uses native Calendar app.",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "events": [],
        }

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "count": len(events),
        "events": events,
    }


def _handle_create(params: dict) -> dict:
    """Create a new calendar event.

    Args:
        params: Must contain 'title', 'start', and 'end' in ISO format.

    Returns:
        Dict with status and the created event details.

    Raises:
        ValueError: If required params are missing or end <= start.
        RuntimeError: If AppleScript execution fails.
    """
    title = params.get("title")
    start = params.get("start")
    end = params.get("end")

    if not title:
        raise ValueError("title is required for create operation")
    if not start:
        raise ValueError("start is required for create operation")
    if not end:
        raise ValueError("end is required for create operation")

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    if end_dt <= start_dt:
        raise ValueError("End time must be after start time")

    if sys.platform != "darwin":
        return {
            "status": "unsupported",
            "note": "Calendar event creation is currently supported only on macOS.",
            "event": {"title": title, "start": start, "end": end},
        }

    start_fmt = start_dt.strftime("%m/%d/%Y %I:%M:%S %p")
    end_fmt = end_dt.strftime("%m/%d/%Y %I:%M:%S %p")

    script = f'''
    tell application "Calendar"
        tell calendar 1
            set newEvent to make new event with properties {{summary:"{title}", start date:date "{start_fmt}", end date:date "{end_fmt}"}}
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

    return {
        "status": "created",
        "event": {"title": title, "start": start, "end": end},
    }


def _handle_delete(params: dict) -> dict:
    """Delete a calendar event by its identifier.

    Args:
        params: Must contain 'event_id' (title/summary on macOS).

    Returns:
        Dict with status and deleted event ID.

    Raises:
        ValueError: If event_id is missing.
        RuntimeError: If deletion fails or event is not found.
    """
    event_id = params.get("event_id")
    if not event_id:
        raise ValueError("event_id is required for delete operation")

    if sys.platform != "darwin":
        return {
            "status": "unsupported",
            "note": "Calendar event deletion is currently supported only on macOS.",
            "event_id": event_id,
        }

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

    return {"status": "deleted", "event_id": event_id}


HANDLERS = {
    "list": _handle_list,
    "create": _handle_create,
    "delete": _handle_delete,
}


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        operation = params.get("operation", "")
        if operation not in VALID_OPERATIONS:
            raise ValueError(
                f"Invalid operation: '{operation}'. Must be one of: {', '.join(sorted(VALID_OPERATIONS))}"
            )
        handler = HANDLERS[operation]
        result = handler(params)
        resp = {"id": req.get("id"), "result": json.dumps(result, indent=2)}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
