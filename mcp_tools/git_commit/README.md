# git_commit

Create a commit with a message in a Git repository.

## Parameters

| Name    | Type   | Required | Description                                       |
|---------|--------|----------|---------------------------------------------------|
| token   | string | Yes      | Git access token for authentication               |
| message | string | Yes      | Commit message describing the changes             |
| path    | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", message="Fix login bug", path="/path/to/repo")
# Returns "Committed a1b2c3d4: Fix login bug"
```
