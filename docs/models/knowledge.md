# Knowledge

Requests knowledge results from licensed data providers, returned under `response.results.knowledge` (omitted when none are relevant).

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
