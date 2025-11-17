# WebSearchTool

Web search tool with optional intent-based triggering


## Fields

| Field                                                                       | Type                                                                        | Required                                                                    | Description                                                                 |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `type`                                                                      | *Literal["web_search"]*                                                     | :heavy_check_mark:                                                          | N/A                                                                         |
| `trigger`                                                                   | [Optional[models.Trigger]](../models/trigger.md)                            | :heavy_minus_sign:                                                          | Tool trigger mode: 'intent' lets agent decide, 'force' always uses the tool |