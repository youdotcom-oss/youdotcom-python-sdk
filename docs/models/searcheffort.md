# SearchEffort

This parameter maps to different configurations regarding the depth of research the tool can perform. Its values range from `low`, `medium` to `high`.

Alternatively, use `auto` mode for a more dynamic search approach, allowing the tool the freedom to adjust its subparameters.

## Example Usage

```python
from youdotcom.models import SearchEffort

value = SearchEffort.AUTO
```


## Values

| Name     | Value    |
| -------- | -------- |
| `AUTO`   | auto     |
| `LOW`    | low      |
| `MEDIUM` | medium   |
| `HIGH`   | high     |