# git_checkout

Switch to a different branch or commit in a Git repository.

## Parameters

| Name   | Type   | Required | Description                                       |
|--------|--------|----------|---------------------------------------------------|
| token  | string | Yes      | Git access token for authentication               |
| target | string | Yes      | Branch name or commit SHA to switch to            |
| path   | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", target="feature/new-ui", path="/path/to/repo")
# Returns "Switched to 'feature/new-ui'"
```
