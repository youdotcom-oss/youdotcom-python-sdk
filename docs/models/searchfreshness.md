# SearchFreshness

Specifies the freshness of the results to return. Provide either one of `day`, `week`, `month`, `year`, or a date range string in the format `YYYY-MM-DDtoYYYY-MM-DD`.

When your search query includes a temporal keyword and you also set a freshness parameter, the search will use the broader (i.e., less restrictive) of the two timeframes. For example, if you use `query=news+this+week&freshness=month`, the results will use a freshness of month.


## Supported Types

### `models.Freshness`

```python
value: models.Freshness = /* values here */
```

### `str`

```python
value: str = /* values here */
```

