# AnswerResponse

A synthesized answer with citations and supporting search results.


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | *str* | :heavy_check_mark: | The synthesized response with numbered inline citations that reference items in the `citations` array. |
| `citations` | List[[models.AnswerCitation](../models/answercitation.md)] | :heavy_minus_sign: | The sources cited in the answer, in citation order. |
| `results` | [models.AnswerResults](../models/answerresponse.md) | :heavy_minus_sign: | Search results grouped by result type. Contains a `web` array of [AnswerSearchResult](../models/answersearchresult.md). |
