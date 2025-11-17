# Response


## Fields

| Field                                                      | Type                                                       | Required                                                   | Description                                                | Example                                                    |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| `type`                                                     | *Optional[str]*                                            | :heavy_minus_sign:                                         | The type of the response.                                  | web_search.results, message.answer                         |
| `output_index`                                             | *Optional[int]*                                            | :heavy_minus_sign:                                         | The index of the output in the response.                   | 0                                                          |
| `delta`                                                    | *Optional[str]*                                            | :heavy_minus_sign:                                         | The delta of the response.                                 | pital of France                                            |
| `full`                                                     | [Optional[models.FullResponse]](../models/fullresponse.md) | :heavy_minus_sign:                                         | N/A                                                        |                                                            |