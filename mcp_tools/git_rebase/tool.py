"""Git rebase tool - rebases the current branch onto another branch."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, branch: str, path: str = ".") -> str:
    """
    Rebase the current branch onto another branch.

    @param token: Git access token for authentication.
    @param branch: Branch to rebase onto.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message on successful rebase.
    @throws ValueError: If token or branch is not provided.
    @throws RuntimeError: If the repository is invalid or rebase fails.
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
        repo.git.rebase(branch)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to rebase '{current_branch}' onto '{branch}': {exc}"
        )

    return f"Rebased '{current_branch}' onto '{branch}'"
