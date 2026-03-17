# git_tag

Create a lightweight or annotated tag in a Git repository.

## Parameters

| Name    | Type   | Required | Description                                       |
|---------|--------|----------|---------------------------------------------------|
| token   | string | Yes      | Git access token for authentication               |
| name    | string | Yes      | Tag name                                          |
| message | string | No       | Tag message (creates annotated tag if provided)   |
| path    | string | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", name="v1.0.0", message="Release 1.0.0")
# Returns "Created annotated tag 'v1.0.0'"
```
