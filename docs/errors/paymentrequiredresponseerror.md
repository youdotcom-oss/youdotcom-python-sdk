# PaymentRequiredResponseError

Payment Required (402). The account cannot make paid API requests.


## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | *Optional[str]* | :heavy_minus_sign: | The error code (e.g. `"payment_required"`). |
| `message` | *Optional[str]* | :heavy_minus_sign: | A human-readable description of the error. |
| `upgrade_url` | *Optional[str]* | :heavy_minus_sign: | URL for adding credits or upgrading the account. |
| `limit` | *Optional[int]* | :heavy_minus_sign: | The usage limit, when available. |
| `used` | *Optional[int]* | :heavy_minus_sign: | The usage consumed, when available. |
| `period` | *Optional[str]* | :heavy_minus_sign: | The usage period, when available. |
| `reset_at` | *Optional[str]* | :heavy_minus_sign: | The reset timestamp, when available. |
