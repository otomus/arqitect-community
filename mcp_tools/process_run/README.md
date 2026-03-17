# process_run

Run a system process safely using subprocess. Commands are parsed with `shlex.split` to prevent shell injection -- `shell=True` is never used.

## Parameters

| Name    | Type   | Required | Description                              |
|---------|--------|----------|------------------------------------------|
| command | string | yes      | Command to execute (e.g. 'ls -la /tmp')  |
| timeout | number | no       | Timeout in seconds (default: 30)         |

## Usage

```python
output = run("ls -la /tmp")
output = run("python3 --version", timeout=10)
```
