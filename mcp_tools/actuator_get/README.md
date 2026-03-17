# actuator_get

Get the current state of an IoT actuator via a REST gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| actuator_id | string | Yes | Unique identifier of the actuator |
| device_host | string | No | IoT gateway URL (defaults to SENTIENT_IOT_HOST) |

## Environment Variables

- `SENTIENT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run("relay-001", device_host="http://192.168.1.100:8080")
```
