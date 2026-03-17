# git_branch_list

List local (and optionally remote) branches in a Git repository.

## Parameters

| Name  | Type    | Required | Description                                       |
|-------|---------|----------|---------------------------------------------------|
| token | string  | Yes      | Git access token for authentication               |
| all   | boolean | No       | Include remote branches (default: false)          |
| path  | string  | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", all=True, path="/path/to/repo")
# Returns branch listing with current branch marked by *
```
