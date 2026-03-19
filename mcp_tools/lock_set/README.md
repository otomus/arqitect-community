# lock_set

Set the state of a smart lock (lock or unlock) via a REST gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| device_id | string | Yes | Unique identifier of the smart lock |
| state | string | Yes | Desired state: 'lock' or 'unlock' |
| device_host | string | No | IoT gateway URL (defaults to ARQITECT_IOT_HOST) |

## Environment Variables

- `ARQITECT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run("lock-front-door", "lock", device_host="http://192.168.1.100:8080")
```
