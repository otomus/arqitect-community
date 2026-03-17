# sensor_list

List all available sensors on the IoT gateway.

## Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| device_host | string | No | IoT gateway URL (defaults to SENTIENT_IOT_HOST) |

## Environment Variables

- `SENTIENT_IOT_HOST` - Default IoT gateway URL

## Usage

```python
result = run(device_host="http://192.168.1.100:8080")
```
