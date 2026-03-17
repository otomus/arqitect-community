"""Compute a unified diff between two texts."""

import difflib


def run(old: str, new: str) -> str:
    """Compute a unified diff between old and new text."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile="old", tofile="new")
    result = "".join(diff)
    return result if result else "No differences found."
