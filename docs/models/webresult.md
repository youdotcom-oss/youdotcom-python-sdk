# WebResult


## Fields

| Field                                                                                 | Type                                                                                  | Required                                                                              | Description                                                                           | Example                                                                               |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `url`                                                                                 | *Optional[str]*                                                                       | :heavy_minus_sign:                                                                    | The URL of the specific search result.                                                | https://you.com                                                                       |
| `title`                                                                               | *Optional[str]*                                                                       | :heavy_minus_sign:                                                                    | The title or name of the search result.                                               | The World's Greatest Search Engine!                                                   |
| `description`                                                                         | *Optional[str]*                                                                       | :heavy_minus_sign:                                                                    | A brief description of the content of the search result.                              | Search on YDC                                                                         |
| `snippets`                                                                            | Optional[List[*str*]]                                                                 | :heavy_minus_sign:                                                                    | An array of text snippets from the search result, providing a preview of the content. |                                                                                       |
| `thumbnail_url`                                                                       | *Optional[str]*                                                                       | :heavy_minus_sign:                                                                    | URL of the thumbnail.                                                                 | https://www.somethumbnailsite.com/thumbnail.jpg                                       |
| `page_age`                                                                            | *Union[[datetime](https://docs.python.org/3/library/datetime.html#datetime-objects), str, None]* | :heavy_minus_sign:                                                                    | The age of the search result.                                                         | 2025-06-25T11:41:00                                                                   |
| `contents`                                                                            | [Optional[models.Contents]](../models/contents.md)                                    | :heavy_minus_sign:                                                                    | Contents of the page if `extraction` was enabled (formerly `livecrawl`).              |                                                                                       |
| `favicon_url`                                                                         | *Optional[str]*                                                                       | :heavy_minus_sign:                                                                    | The URL of the favicon of the search result's domain.                                 | https://someurl.com/favicon                                                           |

## Notes

### `page_age` may be a string

`page_age` is `Union[datetime, str, None]`. An ISO 8601 value parses to a
`datetime`; any other string is returned verbatim.

| Value from the API | `result.page_age` |
| ------------------ | ----------------- |
| `"2025-06-25T11:41:00"` (ISO 8601) | `datetime(2025, 6, 25, 11, 41)` |
| `"7/29/2024 10:38:56 AM"` | `"7/29/2024 10:38:56 AM"` |
| `"Mon, 29 Jul 2024 10:38:56 GMT"` | returned verbatim |
| `1721000000` (number, or a numeric string) | `datetime` — read as a Unix epoch |
| a JSON object or array | raises |
| absent | `None` |

Narrow with `isinstance` before using it as a datetime:

```python
from datetime import datetime

for result in res.results.web:
    if isinstance(result.page_age, datetime):
        print(result.page_age.date())
    elif result.page_age:
        print(f"unparsed timestamp: {result.page_age}")
```
