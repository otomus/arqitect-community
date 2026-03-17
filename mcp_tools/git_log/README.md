# git_log

Show commit history of a Git repository.

## Parameters

| Name  | Type    | Required | Description                                       |
|-------|---------|----------|---------------------------------------------------|
| token | string  | Yes      | Git access token for authentication               |
| count | integer | No       | Number of commits to show (default: 10)           |
| path  | string  | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", count=5, path="/path/to/repo")
# Returns formatted commit log with SHA, date, author, and message
```
