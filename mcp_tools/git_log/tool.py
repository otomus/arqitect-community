"""Git log tool - shows commit history of a Git repository."""

from datetime import datetime

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def _format_commit(commit: "git.Commit") -> str:
    """Format a single commit into a human-readable line."""
    authored_date = datetime.fromtimestamp(commit.authored_date).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    summary = commit.summary
    return f"{commit.hexsha[:8]} {authored_date} {commit.author.name}: {summary}"


def run(token: str, count: int = 10, path: str = ".") -> str:
    """
    Show commit history of a Git repository.

    @param token: Git access token for authentication.
    @param count: Number of commits to display (default: 10).
    @param path: Path to the Git repository (default: current directory).
    @returns: Formatted commit log entries.
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

    try:
        commits = list(repo.iter_commits(max_count=count))
    except Exception as exc:
        raise RuntimeError(f"Failed to read commit log: {exc}")

    if not commits:
        return "No commits found"

    lines = [_format_commit(c) for c in commits]
    return "\n".join(lines)
