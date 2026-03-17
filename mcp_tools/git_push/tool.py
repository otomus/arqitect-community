"""Git push tool - pushes commits to a remote repository."""

try:
    import git
except ImportError:
    return "error: " + "GitPython is required. Install it with: pip install GitPython"


def _inject_token(url: str, token: str) -> str:
    """Inject token into HTTPS git URL for authentication."""
    if url.startswith("https://"):
        return url.replace("https://", f"https://{token}@", 1)
    return url


def run(
    token: str,
    remote: str = "origin",
    branch: str = "",
    path: str = ".",
) -> str:
    """
    Push commits to a remote repository.

    Injects the provided token into the remote URL for HTTPS authentication.

    @param token: Git access token for authentication.
    @param remote: Remote name (default: origin).
    @param branch: Branch to push (default: current branch).
    @param path: Path to the Git repository (default: current directory).
    @returns: Confirmation message on successful push.
    @throws ValueError: If token is not provided.
    @throws RuntimeError: If the repository is invalid or push fails.
    """
    if not token:
        raise ValueError("Git token is required for authentication")

    try:
        repo = git.Repo(path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(f"'{path}' is not a valid Git repository")
    except git.NoSuchPathError:
        raise RuntimeError(f"Path '{path}' does not exist")

    remote_obj = repo.remote(remote)
    original_url = remote_obj.url
    authenticated_url = _inject_token(original_url, token)

    try:
        with remote_obj.config_writer as cw:
            cw.set("url", authenticated_url)

        target_branch = branch if branch else repo.active_branch.name
        push_info = remote_obj.push(target_branch)

        return f"Pushed '{target_branch}' to '{remote}' successfully"
    except Exception as exc:
        raise RuntimeError(f"Failed to push: {exc}")
    finally:
        # Restore original URL to avoid leaking tokens in config
        with remote_obj.config_writer as cw:
            cw.set("url", original_url)
