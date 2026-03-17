# process_list

List running system processes with optional filtering.

## Parameters

| Name   | Type   | Required | Description                            |
|--------|--------|----------|----------------------------------------|
| filter | string | no       | Substring to filter process names by   |

## Usage

```python
output = run()                # all processes
output = run(filter="python") # only processes matching 'python'
```
