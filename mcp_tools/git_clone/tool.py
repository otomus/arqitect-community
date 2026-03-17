"""Git clone tool - clones a remote Git repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def _inject_token(url: str, token: str) -> str:
    """Inject token into HTTPS git URL for authentication."""
    if url.startswith("https://"):
        return url.replace("https://", f"https://{token}@", 1)
    return url


def run(token: str, url: str, destination: str = "") -> str:
    """
    Clone a remote Git repository.

    Injects the provided token into the repository URL for HTTPS authentication.

    @param token: Git access token for authentication.
    @param url: Repository URL to clone.
    @param destination: Local directory to clone into (default: derived from URL).
    @returns: Confirmation message with the clone location.
    @throws ValueError: If token or url is not provided.
    @throws RuntimeError: If cloning fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    if not url or not url.strip():
        raise ValueError("Repository URL is required")

    authenticated_url = _inject_token(url, token)

    clone_kwargs = {}
    if destination:
        clone_kwargs["to_path"] = destination

    try:
        if destination:
            repo = git.Repo.clone_from(authenticated_url, destination)
        else:
            # Derive directory name from URL
            repo_name = url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            repo = git.Repo.clone_from(authenticated_url, repo_name)
            destination = repo_name
    except Exception as exc:
        raise RuntimeError(f"Failed to clone repository: {exc}")

    return f"Cloned '{url}' into '{destination}'"
