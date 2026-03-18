"""Install a package using pip, npm, or another package manager."""

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
        version = params.get("version")

        if manager == "pip":
            pkg_spec = f"{name}=={version}" if version else name
            cmd = [sys.executable, "-m", "pip", "install", pkg_spec]
        elif manager == "npm":
            pkg_spec = f"{name}@{version}" if version else name
            cmd = ["npm", "install", pkg_spec]
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
