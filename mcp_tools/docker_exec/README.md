# docker_exec

Execute a command inside a running Docker container.

## Parameters

| Name         | Type   | Required | Description                                    |
|--------------|--------|----------|------------------------------------------------|
| container_id | string | yes      | Container ID or name to execute the command in |
| command      | string | yes      | Command to execute inside the container        |

## Usage

```python
output = run("my_container", "ls -la /app")
output = run("my_container", "cat /etc/hostname")
```
