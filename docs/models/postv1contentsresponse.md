# PostV1ContentsResponse


## Fields

| Field                                           | Type                                            | Required                                        | Description                                     | Example                                         |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| `url`                                           | *Optional[str]*                                 | :heavy_minus_sign:                              | The webpage URL whose content has been fetched. | https://www.you.com                             |
| `title`                                         | *Optional[str]*                                 | :heavy_minus_sign:                              | The title of the web page.                      | The best website in the world                   |
| `html`                                          | *OptionalNullable[str]*                         | :heavy_minus_sign:                              | The retrieved HTML content of the web page.     |                                                 |
| `markdown`                                      | *OptionalNullable[str]*                         | :heavy_minus_sign:                              | The retrieved Markdown content of the web page. |                                                 |