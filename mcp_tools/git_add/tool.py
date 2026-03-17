"""Git add tool - stages specific files for commit."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"

REJECTED_PATTERNS = {".", "-A", "--all"}


def run(token: str, files: str, path: str = ".") -> str:
    """
    Stage specific files for commit in a Git repository.

    Rejects wildcard staging patterns like '.' and '-A' to prevent
    accidentally staging sensitive or unwanted files.

    @param token: Git access token for authentication.
    @param files: Comma-separated file paths to stage.
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message listing staged files.
    @throws ValueError: If token is missing or files contain rejected patterns.
    @throws RuntimeError: If the path is not a valid Git repository.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    file_list = [f.strip() for f in files.split(",") if f.strip()]

    if not file_list:
        raise ValueError("No files specified to stage")

    for file_entry in file_list:
        if file_entry in REJECTED_PATTERNS:
            raise ValueError(
                f"Wildcard staging with '{file_entry}' is not allowed. "
                "Please specify individual file paths."
            )

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        repo.index.add(file_list)
    except Exception as exc:
        raise RuntimeError(f"Failed to stage files: {exc}")

    return f"Staged {len(file_list)} file(s): {', '.join(file_list)}"
