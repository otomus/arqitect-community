# git_push

Push commits to a remote repository with token-based HTTPS authentication.

## Parameters

| Name   | Type   | Required | Description                                       |
|--------|--------|----------|---------------------------------------------------|
| token  | string | Yes      | Git access token for authentication               |
| remote | string | No       | Remote name (default: origin)                     |
| branch | string | No       | Branch to push (default: current branch)          |
| path   | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", remote="origin", branch="main", path="/path/to/repo")
# Returns "Pushed 'main' to 'origin' successfully"
```
