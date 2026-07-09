# OutputSchema

Beta. Requests structured JSON output in output.content using a supported JSON Schema subset. Supported only with research_effort values standard, deep, and exhaustive. Sending output_schema with research_effort: "lite" returns 422.

Schema rules: Root must be a JSON object. Top-level anyOf is not allowed. Every object must define properties and set additionalProperties: false. Every property must be listed in required. Recursive schemas are not supported.

Limits: Max nesting depth 5, max total properties 100, max total enum values 500, max total schema string budget 25,000.


## Fields

| Field       | Type        | Required    | Description |
| ----------- | ----------- | ----------- | ----------- |