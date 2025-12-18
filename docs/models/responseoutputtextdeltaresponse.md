# ResponseOutputTextDeltaResponse


## Fields

| Field                       | Type                        | Required                    | Description                 | Example                     |
| --------------------------- | --------------------------- | --------------------------- | --------------------------- | --------------------------- |
| `output_index`              | *int*                       | :heavy_check_mark:          | N/A                         | 1                           |
| `type`                      | *Literal["message.answer"]* | :heavy_check_mark:          | N/A                         | message.answer              |
| `delta`                     | *str*                       | :heavy_check_mark:          | Incremental text content    |  Test                       |