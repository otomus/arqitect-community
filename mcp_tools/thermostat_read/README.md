# thermostat_read

Read the current temperature and settings from a smart thermostat via a REST gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| device_id | string | Yes | Unique identifier of the thermostat |
| device_host | string | No | IoT gateway URL (defaults to SENTIENT_IOT_HOST) |

## Environment Variables

- `SENTIENT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run("thermostat-living", device_host="http://192.168.1.100:8080")
```
