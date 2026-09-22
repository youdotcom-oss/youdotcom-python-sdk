# AnswerSearchResult

A web search result used during answer synthesis.


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | *str* | :heavy_check_mark: | The URL of the source webpage. |
| `title` | *str* | :heavy_check_mark: | The title of the source webpage. |
| `description` | *Optional[str]* | :heavy_minus_sign: | A brief description of the content of the search result. |
| `snippets` | Optional[List[*str*]] | :heavy_minus_sign: | Text snippets from the search result that preview its content. |
| `thumbnail_url` | *Optional[str]* | :heavy_minus_sign: | URL of the thumbnail. |
| `page_age` | *Optional[str]* | :heavy_minus_sign: | The publication date or age supplied by the search result. |
