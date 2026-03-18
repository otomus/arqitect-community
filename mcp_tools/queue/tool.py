"""Push to or pop from a named queue (JSON lines file)."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

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
        queue = os.path.abspath(params["queue"])

        if operation == "push":
            payload = params["payload"]
            task_id = str(uuid.uuid4())
            entry = {
                "id": task_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": json.loads(payload),
            }
            with open(queue, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            result = task_id

        elif operation == "pop":
            if not os.path.isfile(queue):
                raise ValueError(f"Queue file not found: {queue}")
            with open(queue, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                raise ValueError("Queue is empty")
            first = lines[0].strip()
            remaining = lines[1:]
            with open(queue, "w", encoding="utf-8") as f:
                f.writelines(remaining)
            entry = json.loads(first)
            result = json.dumps(entry)

        else:
            raise ValueError(f"Invalid operation '{operation}'. Must be 'push' or 'pop'.")

        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
