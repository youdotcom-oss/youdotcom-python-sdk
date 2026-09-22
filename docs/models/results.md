# Results

The container for a search response's sections. All three are optional and
independent of each other: the API includes a key only when it has something to
put in it, so any of `web`, `news`, and `knowledge` may be **absent** rather than
present-and-empty, and `results` itself may be omitted. Guard each level before
iterating.

## Example Usage

```python
import os
from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    res = you.search(query="what is the capital of France", knowledge="core")

if res.results:
    for hit in res.results.web or []:
        print(hit.title, hit.url)
    for card in res.results.knowledge or []:
        print(card.title)
```

## Fields

| Field                                              | Type                                                                   | Required                                           | Description                                                                                                                                                                                 |
| -------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `web`                                              | Optional[List[[models.WebResult](../models/webresult.md)]]             | :heavy_minus_sign:                                 | N/A                                                                                                                                                                                         |
| `news`                                             | Optional[List[[models.NewsResult](../models/newsresult.md)]]           | :heavy_minus_sign:                                 | N/A                                                                                                                                                                                         |
| `knowledge`                                        | Optional[List[[models.KnowledgeResult](../models/knowledgeresult.md)]] | :heavy_minus_sign:                                 | Results backed by licensed data providers. Up to 25 are returned, limited to those relevant to the query. When none are relevant the key is omitted rather than returned as an empty array. |