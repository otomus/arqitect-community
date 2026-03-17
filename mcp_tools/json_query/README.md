# json_query

Query JSON using dot-notation paths.

## Usage

```python
result = run('{"user":{"name":"alice"}}', "user.name")
# Returns: "alice"
```