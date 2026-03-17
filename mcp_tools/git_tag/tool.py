"""Git tag tool - creates a tag in a Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def run(token: str, name: str, message: str = "", path: str = ".") -> str:
    """
    Create a tag in a Git repository.

    Creates a lightweight tag by default, or an annotated tag if a message
    is provided.

    @param token: Git access token for authentication.
    @param name: Tag name.
    @param message: Tag message (creates an annotated tag if provided).
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message with the tag name.
    @throws ValueError: If token or name is not provided.
    @throws RuntimeError: If the repository is invalid or tag creation fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not name or not name.strip():
        raise ValueError("Tag name is required")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    try:
        if message:
            repo.create_tag(name, message=message)
            tag_type = "annotated"
        else:
            repo.create_tag(name)
            tag_type = "lightweight"
    except Exception as exc:
        raise RuntimeError(f"Failed to create tag '{name}': {exc}")

    return f"Created {tag_type} tag '{name}'"
