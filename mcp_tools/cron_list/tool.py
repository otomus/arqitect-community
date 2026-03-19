"""List all scheduled cron jobs."""

import json
import os
import sys

JOBS_FILE = os.path.expanduser("~/.arqitect_cron_jobs.json")

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    try:
        jobs = []
        if os.path.isfile(JOBS_FILE):
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                jobs = json.load(f)

        result = json.dumps(jobs)
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
