"""Send a prompt to a local LLM endpoint and return the completion."""

import json
import sys
import urllib.request

LLM_ENDPOINT = "http://127.0.0.1:8080/v1/completions"

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        prompt = params["prompt"]
        temperature = float(params.get("temperature", "0.7"))
        payload = {"prompt": prompt, "temperature": temperature}
        model = params.get("model")
        if model:
            payload["model"] = model
        data = json.dumps(payload).encode("utf-8")
        http_req = urllib.request.Request(
            LLM_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(http_req, timeout=55) as http_resp:
            body = json.loads(http_resp.read().decode("utf-8"))
        result = body.get("choices", [{}])[0].get("text", "")
        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
