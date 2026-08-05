# UnprocessableEntityResponseError

Unprocessable Entity. Invalid request parameter combination.

Handles three possible 422 body shapes:
- `{"error": "..."}` — search spec format
- `{"detail": [{"type": "...", "loc": [...], "msg": "...", ...}]}` — FastAPI validation errors
- `{"errors": [{"status": "422", "code": "...", "title": "...", ...}]}` — JSON:API format


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | *Optional[str]* | :heavy_minus_sign: | Error code from the search spec 422 format. |
| `detail` | *Optional[List[dict]]* | :heavy_minus_sign: | Validation error array from FastAPI's RequestValidationError. |
| `errors` | *Optional[List[dict]]* | :heavy_minus_sign: | JSON:API error array from controller-level error handlers. |