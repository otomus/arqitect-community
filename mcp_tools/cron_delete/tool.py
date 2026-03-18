"""Delete a scheduled cron job by ID."""

import json
import os
import sys

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
        job_id = params["job_id"]

        jobs = []
        if os.path.isfile(JOBS_FILE):
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                jobs = json.load(f)

        original_count = len(jobs)
        jobs = [j for j in jobs if j.get("id") != job_id]

        if len(jobs) == original_count:
            raise ValueError(f"Job not found: {job_id}")

        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)

        result = "ok"
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
