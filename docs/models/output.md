# Output


## Fields

| Field                                                        | Type                                                         | Required                                                     | Description                                                  | Example                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `type`                                                       | *Optional[str]*                                              | :heavy_minus_sign:                                           | The type of the output.                                      | web_search.results, message.answer                           |
| `text`                                                       | *Optional[str]*                                              | :heavy_minus_sign:                                           | The text of the output.                                      | The capital of France is Paris.                              |
| `content`                                                    | [Optional[models.ContentUnion2]](../models/contentunion2.md) | :heavy_minus_sign:                                           | Returns the exact search query or list of sources.           | What is the capital of France?                               |
| `agent`                                                      | *Optional[str]*                                              | :heavy_minus_sign:                                           | The agent used to generate the response.                     | express                                                      |