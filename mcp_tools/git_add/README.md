# git_add

Stage specific files for commit in a Git repository. Rejects wildcard patterns like `.` and `-A` to prevent accidental mass staging.

## Parameters

| Name  | Type   | Required | Description                                              |
|-------|--------|----------|----------------------------------------------------------|
| token | string | Yes      | Git access token for authentication                      |
| files | string | Yes      | Comma-separated file paths to stage                      |
| path  | string | No       | Path to the Git repository (default: current dir)        |

## Usage Example

```python
result = run(token="ghp_xxxx", files="src/main.py, README.md", path="/path/to/repo")
# Returns "Staged 2 file(s): src/main.py, README.md"
```
