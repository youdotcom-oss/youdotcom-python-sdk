# Type

The type of output. This can either be:
* `message.answer` for text responses
* `web_search.results` for output that contains web links. `web_search.results` only appear when you use the `research` tool or express agent with web_search

## Example Usage

```python
from youdotcom.models import Type

value = Type.MESSAGE_ANSWER
```


## Values

| Name                 | Value                |
| -------------------- | -------------------- |
| `MESSAGE_ANSWER`     | message.answer       |
| `WEB_SEARCH_RESULTS` | web_search.results   |