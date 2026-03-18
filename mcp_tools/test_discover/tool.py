"""Discover test files matching a pattern in a directory."""

import fnmatch
import json
import os
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
        pattern = params.get("pattern", "test_*.py")
        resolved = os.path.abspath(path)

        matches = []
        for root, dirs, files in os.walk(resolved):
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(os.path.join(root, filename))

        matches.sort()
        result = json.dumps(matches)
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
