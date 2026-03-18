"""Run tests with coverage reporting."""

import json
import subprocess
import sys

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        path = params.get("path", ".")
        cmd = [
            sys.executable, "-m", "pytest",
            f"--cov={path}",
            "--cov-report=json",
            "--cov-report=term",
            path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=110)
        output = proc.stdout.strip()
        if proc.stderr.strip():
            output += "\n" + proc.stderr.strip()
        result = output
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
