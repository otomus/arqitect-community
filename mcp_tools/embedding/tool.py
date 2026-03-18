"""Create embedding vectors or search a collection by similarity."""

import json
import math
import sys
import urllib.request

EMBEDDING_ENDPOINT = "http://127.0.0.1:8080/v1/embeddings"

sys.stdout.write(json.dumps({"ready": True}) + "\n")
sys.stdout.flush()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    params = req.get("params", {})
    try:
        operation = params.get("operation", "")

        if operation == "create":
            text = params["text"]
            payload: dict = {"input": text}
            model = params.get("model")
            if model:
                payload["model"] = model
            data = json.dumps(payload).encode("utf-8")
            http_req = urllib.request.Request(
                EMBEDDING_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(http_req, timeout=55) as http_resp:
                body = json.loads(http_resp.read().decode("utf-8"))
            embedding = body.get("data", [{}])[0].get("embedding", [])
            result = json.dumps(embedding)

        elif operation == "search":
            query_raw = params["query"]
            collection_path = params["collection"]
            top_k = int(params.get("top_k", "5"))

            try:
                query_vec = json.loads(query_raw)
            except (json.JSONDecodeError, TypeError):
                raise ValueError(
                    "query must be a JSON array representing an embedding vector"
                )

            with open(collection_path, "r", encoding="utf-8") as f:
                collection = json.load(f)

            scored = []
            for item in collection:
                emb = item.get("embedding", [])
                if len(emb) != len(query_vec):
                    continue
                score = cosine_similarity(query_vec, emb)
                scored.append({"score": score, "item": item})

            scored.sort(key=lambda x: x["score"], reverse=True)
            results = scored[:top_k]
            result = json.dumps(results)

        else:
            raise ValueError(f"Invalid operation '{operation}'. Must be 'create' or 'search'.")

        resp = {"id": req.get("id"), "result": result}
    except Exception as e:
        resp = {"id": req.get("id"), "error": str(e)}
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()
