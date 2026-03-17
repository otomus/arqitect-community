# git_status

Get the working tree status of a Git repository using porcelain format.

## Parameters

| Name  | Type   | Required | Description                                      |
|-------|--------|----------|--------------------------------------------------|
| token | string | Yes      | Git access token for authentication              |
| path  | string | No       | Path to the Git repository (default: current dir)|

## Usage Example

```python
result = run(token="ghp_xxxx", path="/path/to/repo")
# Returns porcelain status output or "Working tree is clean"
```
