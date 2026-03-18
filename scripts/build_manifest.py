#!/usr/bin/env python3
"""Build manifest.json from disk contents of mcp_tools/ and nerves/."""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(BASE, "mcp_tools")
NERVES_DIR = os.path.join(BASE, "nerves")
CHECKED_FILES = ["tool.json", "tool.py", "requirements.txt", "tests.json", "README.md"]
DEFAULT_MODEL_SCORES = {"tinylm": 0.5, "small": 0.7, "medium": 0.85, "large": 0.95}


def collect_tools():
    tools = {}
    for name in sorted(os.listdir(TOOLS_DIR)):
        d = os.path.join(TOOLS_DIR, name)
        if not os.path.isdir(d):
            continue
        tj = os.path.join(d, "tool.json")
        if not os.path.exists(tj):
            continue
        with open(tj) as f:
            data = json.load(f)
        files = [fn for fn in CHECKED_FILES if os.path.exists(os.path.join(d, fn))]
        tools[data.get("name", name)] = {
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", ""),
            "runtime": data.get("runtime", "python"),
            "files": files,
        }
    return tools


def collect_nerves():
    nerves = {}
    for name in sorted(os.listdir(NERVES_DIR)):
        d = os.path.join(NERVES_DIR, name)
        if not os.path.isdir(d):
            continue
        bj = os.path.join(d, "bundle.json")
        if not os.path.exists(bj):
            continue
        with open(bj) as f:
            data = json.load(f)
        tool_names = [t["name"] if isinstance(t, dict) else t for t in data.get("tools", [])]
        nerves[data.get("name", name)] = {
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", ""),
            "role": data.get("role", "worker"),
            "tools": tool_names,
            "model_scores": DEFAULT_MODEL_SCORES.copy(),
        }
    return nerves


def main():
    manifest = {
        "version": "2.0",
        "tools": collect_tools(),
        "nerves": collect_nerves(),
    }
    out = os.path.join(BASE, "manifest.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"Wrote {len(manifest['tools'])} tools and {len(manifest['nerves'])} nerves to {out}")


if __name__ == "__main__":
    main()
