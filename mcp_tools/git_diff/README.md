# git_diff

Show changes in the working tree or staging area of a Git repository.

## Parameters

| Name   | Type    | Required | Description                                       |
|--------|---------|----------|---------------------------------------------------|
| token  | string  | Yes      | Git access token for authentication               |
| path   | string  | No       | Path to the Git repository (default: current dir) |
| staged | boolean | No       | Show only staged changes (default: false)         |

## Usage Example

```python
result = run(token="ghp_xxxx", path="/path/to/repo", staged=True)
# Returns diff output or "No changes detected"
```
