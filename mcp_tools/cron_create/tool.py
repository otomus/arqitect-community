"""Create a scheduled job entry in a JSON jobs file."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

JOBS_FILE = os.path.expanduser("~/.sentient_cron_jobs.json")

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        schedule = params["schedule"]
        command = params["command"]
        job_id = str(uuid.uuid4())

        job = {
            "id": job_id,
            "schedule": schedule,
            "command": command,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        jobs = []
        if os.path.isfile(JOBS_FILE):
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                jobs = json.load(f)

        jobs.append(job)

        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)

        result = job_id
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
