"""Record a metric data point to a JSON lines file."""

import json
import os
import sys
from datetime import datetime, timezone

METRICS_FILE = os.path.expanduser("~/.arqitect_metrics.jsonl")

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        name = params["name"]
        value = params["value"]
        tags_raw = params.get("tags")
        tags = json.loads(tags_raw) if tags_raw else {}

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "value": value,
            "tags": tags,
        }

        with open(METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        result = "ok"
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
