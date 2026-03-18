"""Format source code files using ruff or prettier."""

import json
import os
import subprocess
import sys

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()


def detect_language(path):
    """Detect language from file extension."""
    if os.path.isdir(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    if ext in (".py",):
        return "python"
    if ext in (".js", ".jsx", ".ts", ".tsx"):
        return "javascript"
    return None


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        path = params["path"]
        language = params.get("language") or detect_language(path) or "python"

        if language == "python":
            cmd = ["ruff", "format", path]
        elif language == "javascript":
            cmd = ["prettier", "--write", path]
        else:
            raise ValueError(f"Unsupported language: {language}")

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=55)
        output = proc.stdout.strip()
        if proc.stderr.strip():
            output += "\n" + proc.stderr.strip()
        result = output if output else "Formatting complete."
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
