# NewsResult


## Fields

| Field                                                                | Type                                                                 | Required                                                             | Description                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `title`                                                              | *Optional[str]*                                                      | :heavy_minus_sign:                                                   | The title of the news result.                                        |
| `description`                                                        | *Optional[str]*                                                      | :heavy_minus_sign:                                                   | A brief description of the content of the news result.               |
| `page_age`                                                           | [date](https://docs.python.org/3/library/datetime.html#date-objects) | :heavy_minus_sign:                                                   | UTC timestamp of the article's publication date.                     |
| `thumbnail_url`                                                      | *Optional[str]*                                                      | :heavy_minus_sign:                                                   | URL of the thumbnail.                                                |
| `url`                                                                | *Optional[str]*                                                      | :heavy_minus_sign:                                                   | The URL of the news result.                                          |
| `contents`                                                           | [Optional[models.Contents]](../models/contents.md)                   | :heavy_minus_sign:                                                   | Contents of the page if livecrawl was enabled.                       |