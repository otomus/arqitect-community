"""Update a package to its latest version."""

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
        name = params.get("name")
        manager = params.get("manager", "pip")

        if not name:
            raise ValueError("Package name is required for update")

        if manager == "pip":
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", name]
        elif manager == "npm":
            cmd = ["npm", "update", name]
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=110)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        result = proc.stdout.strip()
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
