# docker_build

Build a Docker image from a Dockerfile.

## Parameters

| Name | Type   | Required | Description                                          |
|------|--------|----------|------------------------------------------------------|
| path | string | yes      | Path to the build context containing the Dockerfile  |
| tag  | string | yes      | Tag for the built image (e.g. 'myapp:latest')        |

## Usage

```python
output = run("./my-app", "myapp:latest")
```
