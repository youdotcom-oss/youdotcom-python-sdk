# AnswerResponse

A synthesized answer with citations and supporting search results.

## AnswerResults

Search results grouped by result type.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `web` | List[[models.AnswerSearchResult](../models/answersearchresult.md)] | :heavy_minus_sign: | All web search results considered during answer synthesis. |

## AnswerResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | *str* | :heavy_check_mark: | The synthesized response with numbered inline citations that reference items in the `citations` array. |
| `citations` | List[[models.AnswerCitation](../models/answercitation.md)] | :heavy_minus_sign: | The sources cited in the answer, in citation order. |
| `results` | [models.AnswerResults](#answerresults) | :heavy_minus_sign: | Search results grouped by result type. |
