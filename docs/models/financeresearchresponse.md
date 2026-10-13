# FinanceResearchResponse

A JSON object containing a comprehensive finance-grade answer with citations and supporting search results


## Fields

| Field                                                              | Type                                                               | Required                                                           | Description                                                        |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `output`                                                           | [models.FinanceResearchOutput](../models/financeresearchoutput.md) | :heavy_check_mark:                                                 | The research output containing the answer and sources.             |
| `warnings`                                                         | Optional[List[*str*]]                                               | :heavy_minus_sign:                                                 | Non-fatal warnings generated during the request, such as a deprecation notice for an `output_schema` that will stop being accepted in a future release. `None` when the response omits the key; an empty list when the key is present but no warnings occurred. |