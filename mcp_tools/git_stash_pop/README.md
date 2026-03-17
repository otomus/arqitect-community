# git_stash_pop

Pop a stashed set of changes back into the working directory.

## Parameters

| Name  | Type    | Required | Description                                       |
|-------|---------|----------|---------------------------------------------------|
| token | string  | Yes      | Git access token for authentication               |
| index | integer | No       | Stash index to pop (default: 0)                   |
| path  | string  | No       | Path to the Git repository (default: current dir) |

## Usage Example

```python
result = run(token="ghp_xxxx", index=0, path="/path/to/repo")
# Returns "Popped stash@{0} successfully"
```
