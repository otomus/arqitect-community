"""Git merge tool - merges a branch into the current branch."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, branch: str, path: str = ".") -> str:
    """
    Merge a branch into the current branch.

    @param token: Git access token for authentication.
    @param branch: Branch name to merge into the current branch.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message on successful merge.
    @throws ValueError: If token or branch is not provided.
    @throws RuntimeError: If the repository is invalid or merge fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not branch or not branch.strip():
        raise ValueError("Branch name is required")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    current_branch = repo.active_branch.name

    try:
        repo.git.merge(branch)
    except Exception as exc:
        raise RuntimeError(f"Failed to merge '{branch}' into '{current_branch}': {exc}")

    return f"Merged '{branch}' into '{current_branch}'"
