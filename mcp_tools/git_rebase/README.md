# git_rebase

Rebase the current branch onto another branch in a Git repository.

## Parameters

| Name   | Type   | Required | Description                                       |
|--------|--------|----------|---------------------------------------------------|
| token  | string | Yes      | Git access token for authentication               |
| branch | string | Yes      | Branch to rebase onto                             |
| path   | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", branch="main", path="/path/to/repo")
# Returns "Rebased 'feature/my-work' onto 'main'"
```
