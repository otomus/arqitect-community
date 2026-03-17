"""Git branch create tool - creates a new branch in a Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, name: str, path: str = ".") -> str:
    """
    Create a new branch in a Git repository.

    @param token: Git access token for authentication.
    @param name: Name of the new branch.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message with the new branch name.
    @throws ValueError: If token or name is not provided.
    @throws RuntimeError: If the repository is invalid or branch creation fails.
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
        new_branch = repo.create_head(name)
    except Exception as exc:
        raise RuntimeError(f"Failed to create branch '{name}': {exc}")

    return f"Created branch '{new_branch.name}'"
