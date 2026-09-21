# KnowledgeResult

A single knowledge result. `type` identifies the kind of result and determines which fields it populates. `type`, `title`, and `attribution` are required on every kind.

For `type: answer`, the only kind currently returned, `description` is required and `as_of` is optional.

## Example Usage

```python
import os
from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    res = you.search(query="what is the capital of France", knowledge="core")

    for card in res.results.knowledge or []:
        print(card.type, card.title)
        print(card.description)
        print([credit.name for credit in card.attribution])
```

Knowledge results arrive in the response rather than being constructed by the
caller. Given a raw payload, `KnowledgeResult.model_validate(data)` builds one
from a dict matching `KnowledgeResultTypedDict`.

## Fields

| Field         | Type                                                                   | Required           | Description                                                                                                                                                  | Example                               |
| ------------- | ---------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- |
| `type`        | *str*                                                                  | :heavy_check_mark: | The kind of knowledge result retrieved. `answer` is the only value currently returned. Ignore a value you do not recognize rather than failing on it, since a new kind may populate a different set of fields. | answer                                |
| `title`       | *str*                                                                  | :heavy_check_mark: | The title of the knowledge result.                                                                                                                           | Paris is the capital of France        |
| `attribution` | List[[models.KnowledgeAttribution](../models/knowledgeattribution.md)] | :heavy_check_mark: | Display credit for the data behind the result. These are credits rather than citations: each entry names a provider and carries no URL.                       |                                       |
| `description` | *Optional[str]*                                                        | :heavy_minus_sign: | Description of the knowledge result, drawn from proprietary licensed data. Required on `type: answer` results.                                                | Paris has been the capital of France… |
| `as_of`       | *Optional[str]*                                                        | :heavy_minus_sign: | The date the result's underlying data covers, as `YYYY-MM-DD`. Optional, and omitted when the provider reports no date.                                       | 2026-04-26                            |

## Notes

### The `results.knowledge` key is omitted, not empty

Knowledge results are limited to those relevant to the query. When none are
relevant the API omits `results.knowledge` entirely rather than returning an
empty array, so `response.results.knowledge` is `None` — check for `None`
before iterating.

```python
for card in res.results.knowledge or []:
    print(card.title)
```

### `count` does not cap knowledge

`count` sets the maximum for the web and news sections. Knowledge has its own
limit of up to 25 results, so `count=1` can still return several knowledge
results.

### `type` is a plain string

`type` is modeled as `str` rather than an enum so an unrecognized value parses
instead of raising. A new kind of knowledge result may populate a different
set of fields, so ignore a `type` you do not recognize rather than failing on
it.

### `as_of` is a string, not a date

`as_of` stays a `str` in `YYYY-MM-DD` form, and is `None` when the provider
reports no date. Parse it when you need a date object:

```python
from datetime import datetime

for card in res.results.knowledge or []:
    if card.as_of is not None:
        print(datetime.strptime(card.as_of, "%Y-%m-%d").date())
```
