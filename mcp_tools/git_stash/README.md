# git_stash

Stash changes in the working directory with an optional message.

## Parameters

| Name    | Type   | Required | Description                                       |
|---------|--------|----------|---------------------------------------------------|
| token   | string | Yes      | Git access token for authentication               |
| message | string | No       | Optional message describing the stash             |
| path    | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", message="WIP: login refactor", path="/path/to/repo")
# Returns "Stashed changes successfully"
```
