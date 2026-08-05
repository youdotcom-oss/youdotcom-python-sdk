# InternalServerErrorResponse

Internal Server Error during authentication/authorization middleware.

Handles two possible 500 body shapes:
- `{"detail": "..."}` — plain detail string
- `{"errors": [{"status": "500", "code": "...", "title": "...", ...}]}` — JSON:API format


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail` | *Optional[str]* | :heavy_minus_sign: | A description of the error. |
| `errors` | *Optional[List[dict]]* | :heavy_minus_sign: | JSON:API error array from controller-level error handlers. |