"""Stash or pop changes in a Git working directory."""

try:
    import git
except ImportError:
    git = None


def run(operation: str, message: str = "", ref: str = "") -> str:
    """Stash current changes or pop a stashed set of changes.

    @param operation: 'stash' to save changes, 'pop' to restore them.
    @param message: Description for the stash (stash only).
    @param ref: Stash index to pop (defaults to 0, the most recent).
    @returns Confirmation message.
    @throws ValueError: If the operation is invalid.
    @throws RuntimeError: If the repository is invalid or the git operation fails.
    """
    if operation == "stash":
        return _stash(message)
    if operation == "pop":
        return _pop(ref)
    raise ValueError(f"Invalid operation '{operation}'. Must be 'stash' or 'pop'.")


def _get_repo() -> "git.Repo":
    """Open the Git repository at the current directory."""
    if git is None:
        raise ImportError("GitPython is required. Install it with: pip install GitPython")
    try:
        return git.Repo(".")
    except git.InvalidGitRepositoryError:
        raise RuntimeError("'.' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError("Path '.' does not exist")


def _stash(message: str) -> str:
    """Stash changes in the working directory."""
    repo = _get_repo()
    try:
        if message:
            result = repo.git.stash("push", "-m", message)
        else:
            result = repo.git.stash()
    except Exception as exc:
        raise RuntimeError(f"Failed to stash changes: {exc}")

    if "No local changes to save" in result:
        return "No local changes to stash"

    return "Stashed changes successfully"


def _pop(ref: str) -> str:
    """Pop a stashed set of changes back into the working directory."""
    repo = _get_repo()
    index = int(ref) if ref else 0
    try:
        stash_ref = f"stash@{{{index}}}"
        repo.git.stash("pop", stash_ref)
    except Exception as exc:
        raise RuntimeError(f"Failed to pop stash at index {index}: {exc}")

    return f"Popped stash@{{{index}}} successfully"
