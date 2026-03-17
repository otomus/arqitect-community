"""Git status tool - retrieves the working tree status of a Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, path: str = ".") -> str:
    """
    Get the working tree status of a Git repository.

    @param token: Git access token for authentication.
    @param path: Path to the Git repository (default: current directory).
    @returns: Porcelain-formatted status output, or a message if the tree is clean.
    @throws ValueError: If token is not provided.
    @throws RuntimeError: If the path is not a valid Git repository.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    status_output = repo.git.status("--porcelain")

    if not status_output:
        return "Working tree is clean"

    return status_output
