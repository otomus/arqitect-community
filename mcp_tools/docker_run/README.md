# docker_run

Run a Docker container from a specified image.

## Parameters

| Name   | Type   | Required | Description                              |
|--------|--------|----------|------------------------------------------|
| image  | string | yes      | Docker image to run (e.g. 'nginx:latest') |
| name   | string | no       | Optional name for the container          |
| ports  | string | no       | Port mapping (e.g. '8080:80')            |
| detach | bool   | no       | Run in detached mode (default: true)     |

## Usage

```python
container_id = run("nginx:latest", name="web", ports="8080:80", detach=True)
```
