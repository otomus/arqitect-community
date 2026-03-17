# git_clone

Clone a remote Git repository with token-based HTTPS authentication.

## Parameters

| Name        | Type   | Required | Description                                         |
|-------------|--------|----------|-----------------------------------------------------|
| token       | string | Yes      | Git access token for authentication                 |
| url         | string | Yes      | Repository URL to clone                             |
| destination | string | No       | Local directory to clone into (default: from URL)   |

## Usage Example

```python
result = run(token="ghp_xxxx", url="https://github.com/user/repo.git", destination="./my-repo")
# Returns "Cloned 'https://github.com/user/repo.git' into './my-repo'"
```
