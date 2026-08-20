# AnswerRequestBody

Request body for `POST /v1/answer`.


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | *str* | :heavy_check_mark: | The search query used to retrieve relevant web results. Max 400 characters. Search operators (`site:`, `OR`, etc.) are not supported. |
| `freshness` | [Optional[models.FreshnessValue]](../models/freshnessvalue.md) | :heavy_minus_sign: | Specifies the freshness of the results. One of `day`, `week`, `month`, `year`, or `YYYY-MM-DDtoYYYY-MM-DD`. |
| `country` | [Optional[models.Country]](../models/country.md) | :heavy_minus_sign: | A supported country code that determines the geographical focus of the web results. |
| `language` | [Optional[models.Language]](../models/language.md) | :heavy_minus_sign: | A supported BCP 47 language tag that determines the language of the web results. |
| `safesearch` | [Optional[models.SafeSearch]](../models/safesearch.md) | :heavy_minus_sign: | Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not. |
| `include_domains` | Optional[List[*str*]] | :heavy_minus_sign: | Domains to exclusively include. Cannot combine with `exclude_domains` or `boost_domains`. Max 500. |
| `exclude_domains` | Optional[List[*str*]] | :heavy_minus_sign: | Domains to exclude. Cannot combine with `include_domains`. Can combine with `boost_domains`. Max 500. |
| `boost_domains` | Optional[List[*str*]] | :heavy_minus_sign: | Domains to prefer in ranking. Cannot combine with `include_domains`. Can combine with `exclude_domains`. Max 500. |
