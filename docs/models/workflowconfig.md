# WorkflowConfig

Defines the maximum number of steps the agent uses in its workflow plan to answer your query. Higher values allow for more tool calls, but it takes longer for the agent to provide the response. For instance, setting max_workflow_steps=5 could allow the agent to call the research tool 3 times and the compute tool 2 times.


## Fields

| Field                | Type                 | Required             | Description          | Example              |
| -------------------- | -------------------- | -------------------- | -------------------- | -------------------- |
| `max_workflow_steps` | *Optional[int]*      | :heavy_minus_sign:   | N/A                  | 10                   |