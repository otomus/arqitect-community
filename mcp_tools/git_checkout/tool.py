"""Git checkout tool - switches to a different branch or commit."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, target: str, path: str = ".") -> str:
    """
    Switch to a different branch or commit.

    @param token: Git access token for authentication.
    @param target: Branch name or commit SHA to switch to.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message indicating the new HEAD.
    @throws ValueError: If token or target is not provided.
    @throws RuntimeError: If the repository is invalid or checkout fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not target or not target.strip():
        raise ValueError("Checkout target is required")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        repo.git.checkout(target)
    except Exception as exc:
        raise RuntimeError(f"Failed to checkout '{target}': {exc}")

    return f"Switched to '{target}'"
