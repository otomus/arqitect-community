# password_generate

Generate secure passwords.

## Usage

```python
password = run()                              # 20 chars, ascii
password = run(length=32, charset="hex")      # 32 hex chars
password = run(length=16, charset="alphanumeric")  # no symbols
```