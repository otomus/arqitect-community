"""Count approximate tokens in text using whitespace and punctuation splitting."""

import json
import re
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
        text = params["text"]
        tokens = re.findall(r"\w+|[^\w\s]", text)
        result = str(len(tokens))
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
