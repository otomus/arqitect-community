# device_status

Get the status of a connected IoT device via a REST gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| device_id | string | Yes | Unique identifier of the device |
| device_host | string | No | IoT gateway URL (defaults to SENTIENT_IOT_HOST) |

## Environment Variables

- `SENTIENT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run("sensor-hub-01", device_host="http://192.168.1.100:8080")
```
