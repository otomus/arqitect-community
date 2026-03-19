"""
Migrate mcp_tools from meta.json to tool.json format.

Converts each tool's meta.json into tool.json with:
- "params" dict (converted from "parameters" array)
- "runtime", "entry", "timeout" fields added
- All original meta.json fields preserved

Also updates manifest.json tool entries with "runtime" and "files" fields.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_TOOLS_DIR = os.path.join(BASE_DIR, "mcp_tools")
MANIFEST_PATH = os.path.join(BASE_DIR, "manifest.json")


def convert_parameters_to_params(parameters: list[dict]) -> dict:
    """
    Convert parameters array format to params dict format.

    Args:
        parameters: List of parameter dicts with name, type, description keys.

    Returns:
        Dict mapping param name to {type, description} plus optional fields.
    """
    params = {}
    for param in parameters:
        name = param["name"]
        entry = {
            "type": param.get("type", "string"),
            "description": param.get("description", ""),
        }
        if "required" in param:
            entry["required"] = param["required"]
        if "default" in param:
            entry["default"] = param["default"]
        params[name] = entry
    return params


def build_tool_json(meta: dict) -> dict:
    """
    Build tool.json content from meta.json data.

    Preserves all original fields and adds runtime/entry/timeout/params.

    Args:
        meta: Parsed meta.json content.

    Returns:
        Dict suitable for writing as tool.json.
    """
    tool = {
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "params": convert_parameters_to_params(meta.get("parameters", [])),
        "runtime": "python",
        "entry": "tool.py",
        "timeout": 30,
        "author": meta.get("author", "arqitect-community"),
    }

    # Preserve all extra fields from meta.json
    preserved_keys = {"category", "tags", "requires_api_key", "dependencies", "implementations"}
    for key in preserved_keys:
        if key in meta:
            tool[key] = meta[key]

    return tool


def migrate_tool_directory(tool_dir: str) -> str | None:
    """
    Migrate a single tool directory from meta.json to tool.json.

    Args:
        tool_dir: Absolute path to the tool directory.

    Returns:
        Tool name on success, None if no meta.json found.
    """
    meta_path = os.path.join(tool_dir, "meta.json")
    tool_json_path = os.path.join(tool_dir, "tool.json")

    if not os.path.isfile(meta_path):
        return None

    with open(meta_path, "r") as f:
        meta = json.load(f)

    tool_json = build_tool_json(meta)

    with open(tool_json_path, "w") as f:
        json.dump(tool_json, f, indent=2)
        f.write("\n")

    os.remove(meta_path)
    return meta["name"]


def update_manifest(manifest_path: str) -> int:
    """
    Add runtime and files fields to each tool entry in manifest.json.

    Args:
        manifest_path: Path to manifest.json.

    Returns:
        Number of tool entries updated.
    """
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    tools = manifest.get("tools", {})
    updated = 0

    for tool_name, tool_entry in tools.items():
        tool_entry["runtime"] = "python"
        tool_entry["files"] = ["tool.json", "tool.py", "tests.json"]
        updated += 1

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    return updated


def main() -> None:
    """Run the full migration: convert all meta.json files and update manifest."""
    migrated = []
    skipped = []

    for entry in sorted(os.listdir(MCP_TOOLS_DIR)):
        tool_dir = os.path.join(MCP_TOOLS_DIR, entry)
        if not os.path.isdir(tool_dir):
            continue

        name = migrate_tool_directory(tool_dir)
        if name:
            migrated.append(name)
        else:
            skipped.append(entry)

    print(f"Migrated {len(migrated)} tools to tool.json")
    if skipped:
        print(f"Skipped {len(skipped)} directories (no meta.json): {skipped}")

    updated = update_manifest(MANIFEST_PATH)
    print(f"Updated {updated} manifest entries with runtime and files fields")


if __name__ == "__main__":
    main()
