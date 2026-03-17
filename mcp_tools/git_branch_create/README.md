# git_branch_create

Create a new branch in a Git repository.

## Parameters

| Name  | Type   | Required | Description                                       |
|-------|--------|----------|---------------------------------------------------|
| token | string | Yes      | Git access token for authentication               |
| name  | string | Yes      | Name of the new branch                            |
| path  | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", name="feature/new-login", path="/path/to/repo")
# Returns "Created branch 'feature/new-login'"
```
