# KnowledgeAttribution

Display credit for the data behind a [KnowledgeResult](../models/knowledgeresult.md).

## Example Usage

```python
from youdotcom.models import KnowledgeAttribution

credit = KnowledgeAttribution.model_validate({"name": "Encyclopedia Britannica"})

print(credit.name)              # "Encyclopedia Britannica"
print(credit.source_description)  # None when the provider reports none
```

Attribution entries arrive nested under `KnowledgeResult.attribution`. Given a
raw payload, `KnowledgeAttribution.model_validate(data)` builds one from a dict
matching `KnowledgeAttributionTypedDict`.

## Fields

| Field                | Type            | Required           | Description                             | Example                 |
| -------------------- | --------------- | ------------------ | --------------------------------------- | ----------------------- |
| `name`               | *str*           | :heavy_check_mark: | Data provider for the knowledge result. | Encyclopedia Britannica |
| `source_description` | *Optional[str]* | :heavy_minus_sign: | Description of the provider.            | General knowledge       |

## Notes

These are credits rather than citations: each entry names a provider and
carries no URL. Read them off a result with
`[credit.name for credit in card.attribution]`.
