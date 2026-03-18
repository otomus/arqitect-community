"""Unified reminder management: create, list, and complete reminders.

Uses a JSON file at ~/.sentient_reminders.json as the reminder store.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

REMINDERS_FILE = os.path.expanduser("~/.sentient_reminders.json")

VALID_OPERATIONS = {"create", "list", "complete"}


def _load_reminders() -> list:
    """Load reminders from the JSON store file.

    Returns:
        List of reminder dictionaries.
    """
    if not os.path.exists(REMINDERS_FILE):
        return []
    with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_reminders(reminders: list) -> None:
    """Persist reminders to the JSON store file.

    Args:
        reminders: List of reminder dictionaries to save.
    """
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=2)


def _handle_create(params: dict) -> dict:
    """Create a new reminder.

    Args:
        params: Must contain 'title'; optionally 'due' and 'list_name'.

    Returns:
        Dict with status and the created reminder.
    """
    title = params.get("title")
    if not title:
        raise ValueError("title is required for create operation")

    reminders = _load_reminders()
    reminder = {
        "id": str(uuid.uuid4()),
        "title": title,
        "due": params.get("due", ""),
        "list_name": params.get("list_name", "default"),
        "completed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reminders.append(reminder)
    _save_reminders(reminders)
    return {"status": "created", "reminder": reminder}


def _handle_list(params: dict) -> dict:
    """List reminders, optionally filtered by list_name and completion status.

    Args:
        params: Optionally contains 'list_name' and 'completed'.

    Returns:
        Dict with matching reminders.
    """
    reminders = _load_reminders()
    list_name = params.get("list_name", "")
    completed_filter = params.get("completed", "")

    results = []
    for reminder in reminders:
        if list_name and reminder.get("list_name", "") != list_name:
            continue
        if completed_filter:
            is_completed = reminder.get("completed", False)
            if completed_filter.lower() == "true" and not is_completed:
                continue
            if completed_filter.lower() == "false" and is_completed:
                continue
        results.append(reminder)

    return {"status": "ok", "count": len(results), "reminders": results}


def _handle_complete(params: dict) -> dict:
    """Mark a reminder as completed.

    Args:
        params: Must contain 'id'.

    Returns:
        Dict with status and the completed reminder.
    """
    reminder_id = params.get("id")
    if not reminder_id:
        raise ValueError("id is required for complete operation")

    reminders = _load_reminders()
    for reminder in reminders:
        if reminder["id"] == reminder_id:
            reminder["completed"] = True
            reminder["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save_reminders(reminders)
            return {"status": "completed", "reminder": reminder}

    raise ValueError(f"Reminder not found: {reminder_id}")


HANDLERS = {
    "create": _handle_create,
    "list": _handle_list,
    "complete": _handle_complete,
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
