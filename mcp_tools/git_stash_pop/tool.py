"""Git stash pop tool - pops a stashed set of changes."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, index: int = 0, path: str = ".") -> str:
    """
    Pop a stashed set of changes back into the working directory.

    @param token: Git access token for authentication.
    @param index: Stash index to pop (default: 0, the most recent stash).
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message on successful pop.
    @throws ValueError: If token is not provided.
    @throws RuntimeError: If the repository is invalid or pop fails.
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
        stash_ref = f"stash@{{{index}}}"
        repo.git.stash("pop", stash_ref)
    except Exception as exc:
        raise RuntimeError(f"Failed to pop stash at index {index}: {exc}")

    return f"Popped stash@{{{index}}} successfully"
