"""Git stash tool - stashes changes in the working directory."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, message: str = "", path: str = ".") -> str:
    """
    Stash changes in the working directory.

    @param token: Git access token for authentication.
    @param message: Optional message describing the stash.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message on successful stash.
    @throws ValueError: If token is not provided.
    @throws RuntimeError: If the repository is invalid or stash fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        if message:
            result = repo.git.stash("push", "-m", message)
        else:
            result = repo.git.stash()
    except Exception as exc:
        raise RuntimeError(f"Failed to stash changes: {exc}")

    if "No local changes to save" in result:
        return "No local changes to stash"

    return f"Stashed changes successfully"
