"""Git branch delete tool - deletes a branch from a Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, name: str, force: bool = False, path: str = ".") -> str:
    """
    Delete a branch from a Git repository.

    @param token: Git access token for authentication.
    @param name: Name of the branch to delete.
    @param force: Force delete even if the branch is not fully merged.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message.
    @throws ValueError: If token or name is not provided.
    @throws RuntimeError: If the repository is invalid or deletion fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not name or not name.strip():
        raise ValueError("Branch name is required")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        repo.delete_head(name, force=force)
    except Exception as exc:
        raise RuntimeError(f"Failed to delete branch '{name}': {exc}")

    return f"Deleted branch '{name}'"
