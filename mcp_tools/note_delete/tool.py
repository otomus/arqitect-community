"""Delete a note by its identifier using the platform-specific notes app."""

import json
import subprocess
import sys


def run(note_id: str) -> str:
    """Delete a note from the local notes application.

    On macOS, removes the note from Apple Notes via AppleScript
    by matching the note name.

    @param note_id: The note identifier (name/title on macOS).
    @returns JSON string confirming deletion.
    @throws RuntimeError: If deletion fails or note is not found.
    """
    if sys.platform != "darwin":
        return json.dumps({
            "status": "unsupported",
            "note": "Note deletion is currently supported only on macOS (Apple Notes).",
            "note_id": note_id,
        }, indent=2)

    script = f'''
    tell application "Notes"
        set matchedNotes to (every note whose name is "{note_id}")
        if (count of matchedNotes) is 0 then
            return "not_found"
        end if
        repeat with n in matchedNotes
            delete n
        end repeat
        return "deleted"
    end tell
    '''

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to delete note: {result.stderr.strip()}")

    output = result.stdout.strip()

    if output == "not_found":
        raise RuntimeError(f"Note not found: {note_id}")

    return json.dumps({
        "status": "deleted",
        "note_id": note_id,
    }, indent=2)
