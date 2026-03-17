"""Git branch list tool - lists branches in a Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, all: bool = False, path: str = ".") -> str:
    """
    List branches in a Git repository.

    @param token: Git access token for authentication.
    @param all: If True, include remote-tracking branches.
    @param path: Path to the Git repository (default: current directory).
    @returns: Newline-separated list of branch names, with current branch marked.
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

    lines = []
    active_branch_name = repo.active_branch.name

    for branch in repo.branches:
        prefix = "* " if branch.name == active_branch_name else "  "
        lines.append(f"{prefix}{branch.name}")

    if all:
        for remote in repo.remotes:
            for ref in remote.refs:
                lines.append(f"  remotes/{ref.name}")

    if not lines:
        return "No branches found"

    return "\n".join(lines)
