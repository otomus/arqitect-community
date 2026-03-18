"""List project dependencies from requirements.txt or package.json."""

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
        path = os.path.abspath(params["path"])
        deps = []

        req_file = os.path.join(path, "requirements.txt")
        pkg_file = os.path.join(path, "package.json")

        if os.path.isfile(req_file):
            with open(req_file, "r", encoding="utf-8") as f:
                for dep_line in f:
                    dep_line = dep_line.strip()
                    if dep_line and not dep_line.startswith("#"):
                        deps.append(dep_line)

        if os.path.isfile(pkg_file):
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            for section in ("dependencies", "devDependencies"):
                if section in pkg:
                    for name, version in pkg[section].items():
                        deps.append(f"{name}@{version}")

        if not deps:
            result = "No dependency files found (requirements.txt or package.json)."
        else:
            result = json.dumps(deps)
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
