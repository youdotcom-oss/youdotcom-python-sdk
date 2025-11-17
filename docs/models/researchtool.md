# ResearchTool

Research tool with configurable search effort and report verbosity


## Fields

| Field                                                            | Type                                                             | Required                                                         | Description                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| `type`                                                           | *Literal["research"]*                                            | :heavy_check_mark:                                               | N/A                                                              |
| `search_effort`                                                  | [Optional[models.SearchEffort]](../models/searcheffort.md)       | :heavy_minus_sign:                                               | Search effort level for research: 'auto' lets agent decide       |
| `report_verbosity`                                               | [Optional[models.ReportVerbosity]](../models/reportverbosity.md) | :heavy_minus_sign:                                               | N/A                                                              |