"""Git commit tool - creates a commit with a message."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, message: str, path: str = ".") -> str:
    """
    Create a commit with the staged changes.

    @param token: Git access token for authentication.
    @param message: Commit message describing the changes.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation with the commit SHA and message.
    @throws ValueError: If token or message is not provided.
    @throws RuntimeError: If the path is not a valid Git repository or commit fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not message or not message.strip():
        raise ValueError("Commit message is required")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        commit = repo.index.commit(message)
    except Exception as exc:
        raise RuntimeError(f"Failed to create commit: {exc}")

    return f"Committed {commit.hexsha[:8]}: {message}"
