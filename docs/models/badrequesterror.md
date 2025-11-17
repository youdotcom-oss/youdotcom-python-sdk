# BadRequestError


## Fields

| Field                                          | Type                                           | Required                                       | Description                                    | Example                                        |
| ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| `status`                                       | *str*                                          | :heavy_check_mark:                             | N/A                                            | 400                                            |
| `code`                                         | *str*                                          | :heavy_check_mark:                             | N/A                                            | bad_request                                    |
| `title`                                        | *str*                                          | :heavy_check_mark:                             | N/A                                            | Invalid request body                           |
| `detail`                                       | *str*                                          | :heavy_check_mark:                             | N/A                                            | The field 'tools' must be an array of objects. |