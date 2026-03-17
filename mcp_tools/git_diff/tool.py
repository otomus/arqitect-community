"""Git diff tool - shows changes in the working tree or staging area."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, path: str = ".", staged: bool = False) -> str:
    """
    Show changes in the working tree or staging area.

    @param token: Git access token for authentication.
    @param path: Path to the Git repository (default: current directory).
    @param staged: If True, show only staged (cached) changes.
    @returns: Diff output, or a message if there are no changes.
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

    if staged:
        diff_output = repo.git.diff("--cached")
    else:
        diff_output = repo.git.diff()

    if not diff_output:
        return "No changes detected"

    return diff_output
