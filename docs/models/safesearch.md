# SafeSearch

Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not.

## Example Usage

```python
from youdotcom.models import SafeSearch

value = SafeSearch.OFF
```


## Values

| Name       | Value      |
| ---------- | ---------- |
| `OFF`      | off        |
| `MODERATE` | moderate   |
| `STRICT`   | strict     |