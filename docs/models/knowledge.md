# Knowledge

Requests knowledge results alongside web and news search.

## Example Usage

```python
from youdotcom.models import Knowledge

value = Knowledge.CORE
```


## Values

| Name   | Value |
| ------ | ----- |
| `CORE` | core  |

## Notes

`core` is the only value the API accepts. Passing anything else raises
`ValidationError` locally rather than reaching the network, mirroring the
server's `422`.
