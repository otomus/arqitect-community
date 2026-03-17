# docker_logs

Get logs from a Docker container.

## Parameters

| Name         | Type   | Required | Description                                  |
|--------------|--------|----------|----------------------------------------------|
| container_id | string | yes      | Container ID or name to get logs from        |
| tail         | number | no       | Number of lines to show from end of logs     |

## Usage

```python
logs = run("my_container")
logs = run("my_container", tail=50)
```
