"""Show metadata for an installed package."""

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
        name = params["name"]
        manager = params.get("manager", "pip")

        if manager == "pip":
            cmd = [sys.executable, "-m", "pip", "show", name]
        elif manager == "npm":
            cmd = ["npm", "view", name, "--json"]
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        result = proc.stdout.strip()
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
