"""Run tests using pytest or another test framework."""

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
        pattern = params.get("pattern")
        framework = params.get("framework", "pytest")

        if framework == "pytest":
            cmd = [sys.executable, "-m", "pytest", path, "-v", "--tb=short"]
            if pattern:
                cmd.extend(["-k", pattern])
        elif framework == "unittest":
            cmd = [sys.executable, "-m", "unittest", "discover", "-s", path, "-v"]
            if pattern:
                cmd.extend(["-p", pattern])
        else:
            raise ValueError(f"Unsupported framework: {framework}")

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
