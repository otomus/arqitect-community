"""Database execute tool — runs INSERT/UPDATE/DELETE and returns affected row count."""

import json
import os
import sqlite3
import sys

_CONN_FILE = os.path.expanduser("~/.arqitect_db_connections.json")


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
        sql: str = params["sql"]
        bind_params_raw: str = params.get("params", "[]")
        bind_params: list = json.loads(bind_params_raw) if bind_params_raw else []

        conn = _get_connection(connection_id)
        cursor = conn.execute(sql, bind_params)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        resp = {"id": req.get("id"), "result": {"affected_rows": affected}}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
