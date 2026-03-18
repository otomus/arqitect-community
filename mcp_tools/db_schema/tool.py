"""Database schema tool — returns column names and types for one or all tables."""

import json
import os
import sqlite3
import sys

_CONN_FILE = os.path.expanduser("~/.sentient_db_connections.json")


def _get_connection(connection_id: str) -> sqlite3.Connection:
    """Open a fresh SQLite connection by reading the file-based connection registry."""
    if not os.path.exists(_CONN_FILE):
        raise RuntimeError("No connections. Call db_connect first.")
    with open(_CONN_FILE) as f:
        data = json.load(f)
    if connection_id not in data:
        raise ValueError(f"Unknown connection_id: {connection_id}")
    url = data[connection_id]["url"]
    return sqlite3.connect(url)


def _get_table_schema(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Return a list of column dicts for the given table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return [
        {"name": row[1], "type": row[2], "notnull": bool(row[3]), "primary_key": bool(row[5])}
        for row in cursor.fetchall()
    ]


sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        connection_id: str = params["connection_id"]
        table: str | None = params.get("table")

        conn = _get_connection(connection_id)

        if table:
            schema = {table: _get_table_schema(conn, table)}
        else:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            schema = {t: _get_table_schema(conn, t) for t in tables}

        conn.close()

        resp = {"id": req.get("id"), "result": {"schema": schema}}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
