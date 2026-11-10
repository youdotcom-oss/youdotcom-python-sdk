# ParseEffort

How much effort the Extract API spends parsing PDF pages. It has no effect on web pages.

Available levels:
- `lite`: Extracts the content embedded in each page. Suits digitally created PDFs, such as a text-based contract, at the lowest cost.
- `standard`: The default. Also sends complex pages, such as charts and images, through an advanced model, and is billed per PDF page. Use it when you want the most complete output.

## Example Usage

```python
from youdotcom.models import ParseEffort

value = ParseEffort.LITE
```


## Values

| Name       | Value    |
| ---------- | -------- |
| `LITE`     | lite     |
| `STANDARD` | standard |
