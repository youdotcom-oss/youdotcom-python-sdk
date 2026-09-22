# ResearchResponse


## Fields

| Field      | Type                                 | Required           | Description                                                                                                                     |
|------------|--------------------------------------|--------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `output`   | [models.Output](../models/output.md) | :heavy_check_mark: | The research output containing the answer and sources.                                                                          |
| `warnings` | Optional[List[*str*]]                | :heavy_minus_sign: | A list of warnings generated during research, such as source access issues or partial results. Empty when no warnings occurred. |