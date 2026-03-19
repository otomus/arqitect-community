"""Create and record an alert with severity level."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

ALERTS_FILE = os.path.expanduser("~/.arqitect_alerts.json")

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        title = params["title"]
        body = params["body"]
        severity = params.get("severity", "info")
        alert_id = str(uuid.uuid4())

        alert = {
            "id": alert_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "body": body,
            "severity": severity,
        }

        # Load existing alerts
        alerts = []
        if os.path.isfile(ALERTS_FILE):
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                alerts = json.load(f)

        alerts.append(alert)

        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2)

        sys.stderr.write(f"ALERT [{severity.upper()}]: {title} - {body}\n")
        sys.stderr.flush()

        result = alert_id
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
