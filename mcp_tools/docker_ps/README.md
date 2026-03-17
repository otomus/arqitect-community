# docker_ps

List Docker containers.

## Parameters

| Name | Type | Required | Description                                |
|------|------|----------|--------------------------------------------|
| all  | bool | no       | Show all containers including stopped ones |

## Usage

```python
output = run()          # running containers only
output = run(all=True)  # include stopped containers
```
