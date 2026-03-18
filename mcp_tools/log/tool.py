"""Read from or write to a log file."""

import json
import os
import sys
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
        source = os.path.abspath(params["source"])

        if operation == "read":
            count = int(params.get("count", "100"))
            filter_str = params.get("filter")

            with open(source, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            tail = all_lines[-count:] if count < len(all_lines) else all_lines

            if filter_str:
                tail = [l for l in tail if filter_str in l]

            result = "".join(tail)

        elif operation == "write":
            message = params["message"]
            level = params.get("level", "INFO").upper()
            timestamp = datetime.now(timezone.utc).isoformat()
            entry = f"[{timestamp}] [{level}] {message}\n"

            with open(source, "a", encoding="utf-8") as f:
                f.write(entry)

            result = "ok"

        else:
            raise ValueError(f"Invalid operation '{operation}'. Must be 'read' or 'write'.")

        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
