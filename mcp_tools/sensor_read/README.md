# sensor_read

Read the current value from an IoT sensor via a REST gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| sensor_id | string | Yes | Unique identifier of the sensor |
| device_host | string | No | IoT gateway URL (defaults to SENTIENT_IOT_HOST) |

## Environment Variables

- `SENTIENT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run("temp-001", device_host="http://192.168.1.100:8080")
```
