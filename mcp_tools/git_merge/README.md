# git_merge

Merge a branch into the current branch of a Git repository.

## Parameters

| Name   | Type   | Required | Description                                       |
|--------|--------|----------|---------------------------------------------------|
| token  | string | Yes      | Git access token for authentication               |
| branch | string | Yes      | Branch name to merge into the current branch      |
| path   | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", branch="feature/login", path="/path/to/repo")
# Returns "Merged 'feature/login' into 'main'"
```
