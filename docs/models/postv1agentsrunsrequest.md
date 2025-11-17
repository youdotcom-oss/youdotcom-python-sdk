# PostV1AgentsRunsRequest


## Fields

| Field                                                          | Type                                                           | Required                                                       | Description                                                    |
| -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- |
| `agent`                                                        | [models.Agent](../models/agent.md)                             | :heavy_check_mark:                                             | Agent type (express, advanced) or custom agent UUID            |
| `input`                                                        | *str*                                                          | :heavy_check_mark:                                             | User input prompt.                                             |
| `stream`                                                       | *Optional[bool]*                                               | :heavy_minus_sign:                                             | N/A                                                            |
| `tools`                                                        | List[[models.Tool](../models/tool.md)]                         | :heavy_minus_sign:                                             | Array of tool configurations                                   |
| `verbosity`                                                    | [Optional[models.Verbosity]](../models/verbosity.md)           | :heavy_minus_sign:                                             | Response verbosity level                                       |
| `workflow_config`                                              | [Optional[models.WorkflowConfig]](../models/workflowconfig.md) | :heavy_minus_sign:                                             | N/A                                                            |