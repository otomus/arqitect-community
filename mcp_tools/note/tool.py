"""Unified note management: create, read, search, update, and delete notes.

Uses a JSON file at ~/.sentient_notes.json as the note store.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

NOTES_FILE = os.path.expanduser("~/.sentient_notes.json")

VALID_OPERATIONS = {"create", "read", "search", "update", "delete"}


def _load_notes() -> list:
    """Load notes from the JSON store file.

    Returns:
        List of note dictionaries.
    """
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_notes(notes: list) -> None:
    """Persist notes to the JSON store file.

    Args:
        notes: List of note dictionaries to save.
    """
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2)


def _handle_create(params: dict) -> dict:
    """Create a new note.

    Args:
        params: Must contain 'title'; optionally 'body' and 'folder'.

    Returns:
        Dict with status and the created note.
    """
    title = params.get("title")
    if not title:
        raise ValueError("title is required for create operation")

    notes = _load_notes()
    note = {
        "id": str(uuid.uuid4()),
        "title": title,
        "body": params.get("body", ""),
        "folder": params.get("folder", "default"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    notes.append(note)
    _save_notes(notes)
    return {"status": "created", "note": note}


def _handle_read(params: dict) -> dict:
    """Read a note by its ID.

    Args:
        params: Must contain 'id'.

    Returns:
        Dict with the found note.
    """
    note_id = params.get("id")
    if not note_id:
        raise ValueError("id is required for read operation")

    notes = _load_notes()
    for note in notes:
        if note["id"] == note_id:
            return {"status": "found", "note": note}

    raise ValueError(f"Note not found: {note_id}")


def _handle_search(params: dict) -> dict:
    """Search notes by query string and/or folder.

    Args:
        params: Optionally contains 'query' and/or 'folder'.

    Returns:
        Dict with matching notes.
    """
    query = (params.get("query") or "").lower()
    folder = params.get("folder", "")
    notes = _load_notes()

    results = []
    for note in notes:
        if folder and note.get("folder", "") != folder:
            continue
        if query:
            title_match = query in note.get("title", "").lower()
            body_match = query in note.get("body", "").lower()
            if not (title_match or body_match):
                continue
        results.append(note)

    return {"status": "ok", "count": len(results), "notes": results}


def _handle_update(params: dict) -> dict:
    """Update an existing note.

    Args:
        params: Must contain 'id'; optionally 'title', 'body', 'folder'.

    Returns:
        Dict with status and the updated note.
    """
    note_id = params.get("id")
    if not note_id:
        raise ValueError("id is required for update operation")

    notes = _load_notes()
    for note in notes:
        if note["id"] == note_id:
            if "title" in params and params["title"]:
                note["title"] = params["title"]
            if "body" in params and params["body"]:
                note["body"] = params["body"]
            if "folder" in params and params["folder"]:
                note["folder"] = params["folder"]
            note["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_notes(notes)
            return {"status": "updated", "note": note}

    raise ValueError(f"Note not found: {note_id}")


def _handle_delete(params: dict) -> dict:
    """Delete a note by its ID.

    Args:
        params: Must contain 'id'.

    Returns:
        Dict with status and the deleted note ID.
    """
    note_id = params.get("id")
    if not note_id:
        raise ValueError("id is required for delete operation")

    notes = _load_notes()
    for i, note in enumerate(notes):
        if note["id"] == note_id:
            deleted = notes.pop(i)
            _save_notes(notes)
            return {"status": "deleted", "note_id": deleted["id"]}

    raise ValueError(f"Note not found: {note_id}")


HANDLERS = {
    "create": _handle_create,
    "read": _handle_read,
    "search": _handle_search,
    "update": _handle_update,
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
