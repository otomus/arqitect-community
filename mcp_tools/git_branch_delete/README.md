# git_branch_delete

Delete a branch from a Git repository, with optional force delete for unmerged branches.

## Parameters

| Name  | Type    | Required | Description                                       |
|-------|---------|----------|---------------------------------------------------|
| token | string  | Yes      | Git access token for authentication               |
| name  | string  | Yes      | Name of the branch to delete                      |
| force | boolean | No       | Force delete even if not fully merged (default: false) |
| path  | string  | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", name="feature/old-branch", force=True)
# Returns "Deleted branch 'feature/old-branch'"
```
