"""Database close tool — removes a connection from the file-based registry."""

import json
import os
import sys

_CONN_FILE = os.path.expanduser("~/.sentient_db_connections.json")


def _remove_connection(connection_id: str) -> None:
    """Remove a connection entry from the file-based registry."""
    if not os.path.exists(_CONN_FILE):
        raise RuntimeError("No connections. Call db_connect first.")
    with open(_CONN_FILE) as f:
        data = json.load(f)
    if connection_id not in data:
        raise ValueError(f"Unknown connection_id: {connection_id}")
    del data[connection_id]
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
        connection_id: str = params["connection_id"]
        _remove_connection(connection_id)

        resp = {"id": req.get("id"), "result": {"status": "closed", "connection_id": connection_id}}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
