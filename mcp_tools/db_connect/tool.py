"""Database connection tool — opens a SQLite connection and returns a connection token."""

import json
import os
import sqlite3
import sys
import uuid

_connections: dict[str, sqlite3.Connection] = {}
_CONN_FILE = os.path.expanduser("~/.arqitect_db_connections.json")


def _save_connection(conn_id: str, url: str) -> None:
    """Persist connection info to a file-based registry so other tool subprocesses can reconnect."""
    data: dict = {}
    if os.path.exists(_CONN_FILE):
        with open(_CONN_FILE) as f:
            data = json.load(f)
    data[conn_id] = {"url": url}
    with open(_CONN_FILE, "w") as f:
        json.dump(data, f)


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        url: str = params["url"]
        # Strip the sqlite:// or sqlite:/// prefix to get the file path.
        if url.startswith("sqlite:///"):
            db_path = url[len("sqlite:///"):]
        elif url.startswith("sqlite://"):
            db_path = url[len("sqlite://"):]
        else:
            db_path = url

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        connection_id = str(uuid.uuid4())
        _connections[connection_id] = conn
        _save_connection(connection_id, db_path)

        resp = {
            "id": req.get("id"),
            "result": {"connection_id": connection_id, "status": "connected", "path": db_path},
        }
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
