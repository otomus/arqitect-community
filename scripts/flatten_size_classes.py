#!/usr/bin/env python3
"""One-shot migration script to flatten size-class directories.

Removes the tinylm/small/medium/large tier structure from nerves and adapters,
promoting the 'large' variant (with fallbacks) to the root level.

Run once, then delete this script.
"""

import json
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIZE_CLASSES = ("large", "medium", "small", "tinylm")


def _load_json(path: str) -> dict | None:
    """Load JSON from path, returning None on failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: str, data: dict) -> None:
    """Write data as formatted JSON to path."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _pick_best_file(parent: str, filename: str) -> str | None:
    """Return the path to filename from the best available size class.

    Prefers large, falls back through medium, small, tinylm.
    """
    for size in SIZE_CLASSES:
        candidate = os.path.join(parent, size, filename)
        if os.path.exists(candidate):
            return candidate
    return None


def _strip_size_fields(meta: dict) -> dict:
    """Remove size_class and model fields from a meta dict."""
    meta.pop("size_class", None)
    meta.pop("model", None)
    return meta


def _collect_model_dirs(parent: str) -> list[tuple[str, str, str]]:
    """Find model-specific directories inside size-class dirs.

    Returns list of (model_name, source_path, size_class).
    """
    results = []
    for size in SIZE_CLASSES:
        size_dir = os.path.join(parent, size)
        if not os.path.isdir(size_dir):
            continue
        for entry in os.listdir(size_dir):
            entry_path = os.path.join(size_dir, entry)
            if os.path.isdir(entry_path) and entry not in SIZE_CLASSES:
                results.append((entry, entry_path, size))
    return results


def _remove_size_dirs(parent: str) -> None:
    """Delete all size-class subdirectories from parent."""
    for size in SIZE_CLASSES:
        size_dir = os.path.join(parent, size)
        if os.path.isdir(size_dir):
            shutil.rmtree(size_dir)


def migrate_nerve(nerve_dir: str) -> bool:
    """Migrate a single nerve directory to flat structure.

    Returns True if migration was performed.
    """
    name = os.path.basename(nerve_dir)

    # Skip if already flat (context.json exists at root)
    if os.path.exists(os.path.join(nerve_dir, "context.json")):
        return False

    # Check if any size dirs exist
    has_sizes = any(
        os.path.isdir(os.path.join(nerve_dir, s)) for s in SIZE_CLASSES
    )
    if not has_sizes:
        return False

    # Promote context.json
    src_context = _pick_best_file(nerve_dir, "context.json")
    if src_context:
        shutil.copy2(src_context, os.path.join(nerve_dir, "context.json"))

    # Promote meta.json (strip size_class and model fields)
    src_meta = _pick_best_file(nerve_dir, "meta.json")
    if src_meta:
        meta = _load_json(src_meta)
        if meta:
            _strip_size_fields(meta)
            _write_json(os.path.join(nerve_dir, "meta.json"), meta)

    _remove_size_dirs(nerve_dir)
    return True


def migrate_adapter(role_dir: str) -> int:
    """Migrate a single adapter role directory to flat structure.

    Returns the number of model-specific adapters moved.
    """
    role = os.path.basename(role_dir)

    # Skip if already flat (context.json exists at role root)
    if os.path.exists(os.path.join(role_dir, "context.json")):
        return 0

    has_sizes = any(
        os.path.isdir(os.path.join(role_dir, s)) for s in SIZE_CLASSES
    )
    if not has_sizes:
        return 0

    # Promote context.json
    src_context = _pick_best_file(role_dir, "context.json")
    if src_context:
        shutil.copy2(src_context, os.path.join(role_dir, "context.json"))

    # Promote meta.json
    src_meta = _pick_best_file(role_dir, "meta.json")
    if src_meta:
        meta = _load_json(src_meta)
        if meta:
            _strip_size_fields(meta)
            _write_json(os.path.join(role_dir, "meta.json"), meta)

    # Promote test_bank.jsonl
    src_test_bank = _pick_best_file(role_dir, "test_bank.jsonl")
    if src_test_bank:
        shutil.copy2(src_test_bank, os.path.join(role_dir, "test_bank.jsonl"))

    # Move model-specific dirs up: role/size/model/ -> role/model/
    model_dirs = _collect_model_dirs(role_dir)
    models_moved = 0
    seen_models = set()
    for model_name, src_path, _size in model_dirs:
        dest = os.path.join(role_dir, model_name)
        if model_name in seen_models:
            continue
        seen_models.add(model_name)
        if not os.path.exists(dest):
            shutil.copytree(src_path, dest)
            models_moved += 1

    _remove_size_dirs(role_dir)
    return models_moved


def main() -> None:
    """Run the migration across all nerves and adapters."""
    nerves_dir = os.path.join(REPO_ROOT, "nerves")
    adapters_dir = os.path.join(REPO_ROOT, "adapters")

    nerves_migrated = 0
    adapters_migrated = 0

    # Migrate nerves
    if os.path.isdir(nerves_dir):
        for name in sorted(os.listdir(nerves_dir)):
            nerve_path = os.path.join(nerves_dir, name)
            if not os.path.isdir(nerve_path):
                continue
            if migrate_nerve(nerve_path):
                nerves_migrated += 1

    # Migrate adapters
    if os.path.isdir(adapters_dir):
        for role in sorted(os.listdir(adapters_dir)):
            role_path = os.path.join(adapters_dir, role)
            if not os.path.isdir(role_path):
                continue
            models = migrate_adapter(role_path)
            adapters_migrated += 1

    print(f"Migration complete: {nerves_migrated} nerves migrated, "
          f"{adapters_migrated} adapters migrated")


if __name__ == "__main__":
    main()
