#!/usr/bin/env python3
"""Generate manifest.json by walking the repo tree.

Reads all bundle.json, meta.json, and connector meta.json files
and builds a unified manifest for discovery and search.
"""

import json
import os
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect_nerves() -> dict:
    """Walk nerves/ and extract bundle info."""
    nerves = {}
    nerves_dir = os.path.join(REPO_ROOT, "nerves")
    if not os.path.isdir(nerves_dir):
        return nerves

    for name in sorted(os.listdir(nerves_dir)):
        bundle_path = os.path.join(nerves_dir, name, "bundle.json")
        if not os.path.exists(bundle_path):
            continue
        try:
            with open(bundle_path) as f:
                bundle = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Extract model scores from model_adapters
        model_scores = {}
        for model, adapter in bundle.get("model_adapters", {}).items():
            if "score" in adapter:
                model_scores[model] = adapter["score"]

        nerves[name] = {
            "description": bundle.get("description", ""),
            "role": bundle.get("role", "tool"),
            "tags": bundle.get("tags", []),
            "authors": bundle.get("authors", []),
            "version": bundle.get("version", "1.0"),
            "tools": [t["name"] for t in bundle.get("tools", [])],
            "model_scores": model_scores,
        }

    return nerves


def collect_adapters() -> dict:
    """Walk adapters/brain/ and extract adapter info."""
    adapters = {}
    adapters_dir = os.path.join(REPO_ROOT, "adapters", "brain")
    if not os.path.isdir(adapters_dir):
        return adapters

    for name in sorted(os.listdir(adapters_dir)):
        meta_path = os.path.join(adapters_dir, name, "meta.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Get score from qualification.json if it exists
        score = None
        qual_path = os.path.join(adapters_dir, name, "qualification.json")
        if os.path.exists(qual_path):
            try:
                with open(qual_path) as f:
                    qual = json.load(f)
                score = qual.get("overall_score")
            except (json.JSONDecodeError, OSError):
                pass

        adapters[name] = {
            "model": meta.get("model", name),
            "size_class": meta.get("size_class", ""),
            "provider": meta.get("provider", ""),
            "score": score,
            "contributor": meta.get("contributor", {}).get("github", ""),
            "has_lora": meta.get("has_lora", False),
        }

    return adapters


def collect_connectors() -> dict:
    """Walk connectors/ and extract connector info."""
    connectors = {}
    connectors_dir = os.path.join(REPO_ROOT, "connectors")
    if not os.path.isdir(connectors_dir):
        return connectors

    for name in sorted(os.listdir(connectors_dir)):
        meta_path = os.path.join(connectors_dir, name, "meta.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        connectors[name] = {
            "name": meta.get("name", name),
            "version": meta.get("version", ""),
            "description": meta.get("description", ""),
            "language": meta.get("language", ""),
            "platforms": meta.get("platforms", []),
            "author": meta.get("author", {}).get("github", ""),
            "capabilities": meta.get("capabilities", {}),
            "config_fields": meta.get("config_fields", []),
        }

    return connectors


def build_leaderboard(adapters: dict) -> dict:
    """Build leaderboard of top adapters by size_class."""
    by_class = {}
    for name, info in adapters.items():
        sc = info.get("size_class", "unknown")
        if info.get("score") is not None:
            by_class.setdefault(sc, []).append({
                "model": info["model"],
                "score": info["score"],
                "contributor": info.get("contributor", ""),
            })

    # Sort each class by score descending
    for sc in by_class:
        by_class[sc].sort(key=lambda x: x["score"], reverse=True)

    return by_class


def main():
    nerves = collect_nerves()
    adapters = collect_adapters()
    connectors = collect_connectors()

    manifest = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "nerves": nerves,
        "adapters": adapters,
        "connectors": connectors,
        "stats": {
            "total_nerves": len(nerves),
            "total_adapters": len(adapters),
            "total_connectors": len(connectors),
        },
        "leaderboard": build_leaderboard(adapters),
    }

    manifest_path = os.path.join(REPO_ROOT, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated manifest.json: {len(nerves)} nerves, {len(adapters)} adapters, {len(connectors)} connectors")


if __name__ == "__main__":
    main()
