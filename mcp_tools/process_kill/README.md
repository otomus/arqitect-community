# process_kill

Kill a process by PID with a specified signal.

## Parameters

| Name   | Type   | Required | Description                                       |
|--------|--------|----------|---------------------------------------------------|
| pid    | number | yes      | Process ID to send the signal to                  |
| signal | string | no       | Signal name: TERM, KILL, HUP, INT, USR1, USR2    |

## Usage

```python
result = run(12345)                  # sends SIGTERM
result = run(12345, signal="KILL")   # sends SIGKILL
```
