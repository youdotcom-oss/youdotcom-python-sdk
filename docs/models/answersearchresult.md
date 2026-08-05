# AnswerSearchResult

A web search result used during answer synthesis.


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | *str* | :heavy_check_mark: | The URL of the source webpage. |
| `title` | *str* | :heavy_check_mark: | The title of the source webpage. |
| `snippets` | Optional[List[*str*]] | :heavy_minus_sign: | Text snippets from the search result that preview its content. |
| `page_age` | *Optional[str]* | :heavy_minus_sign: | The publication date or age supplied by the search result. |
