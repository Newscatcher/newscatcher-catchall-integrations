# Monitor Scheduling Reference

Monitors run a completed job's query on a recurring schedule. They are created
from a reference job and can optionally deliver results to a webhook.

## Creating a monitor

```json
{
  "reference_job_id": "0b5ead06-535e-4bb0-b25d-aaac2293faef",
  "schedule": "every day at 9 AM EST",
  "webhook": {
    "url": "https://your-endpoint.com/hook",
    "method": "POST",
    "headers": { "Authorization": "Bearer your-token" }
  }
}
```

The `reference_job_id` must point to a completed job. The monitor will re-use
that job's query, validators, enrichments, and other parameters for every run.

## Schedule format

Schedules are defined in **natural language**. The system converts them to cron
expressions internally. Always include a timezone.

### Examples

| Natural language schedule | Meaning |
|---|---|
| `"every day at 9 AM EST"` | Daily at 9:00 AM Eastern |
| `"every Monday at 8 AM UTC"` | Weekly on Mondays at 8:00 UTC |
| `"every 6 hours"` | Every 6 hours starting from creation |
| `"every weekday at 7 AM PST"` | Monday–Friday at 7:00 AM Pacific |
| `"every Sunday at 11 PM CET"` | Weekly on Sundays at 23:00 Central European |
| `"twice a day at 8 AM and 6 PM EST"` | Twice daily |
| `"every first Monday of the month at 9 AM UTC"` | Monthly |

### Tips

- Always include a timezone to avoid ambiguity.
- For news monitoring, daily or twice-daily schedules work best — more frequent
  than every 6 hours rarely adds value.
- Consider your audience's timezone when setting delivery times.

## Webhook configuration

The `webhook` field is optional. If omitted, results are available via the
`GET /catchAll/monitors/pull/{monitor_id}` endpoint.

### Full webhook schema

```json
{
  "url": "https://your-endpoint.com/hook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-token",
    "Content-Type": "application/json"
  },
  "params": {
    "source": "catchall"
  },
  "auth": ["username", "password"]
}
```

| Field | Required | Description |
|---|---|---|
| `url` | Yes | Destination URL |
| `method` | No | `POST` (default) or `PUT` |
| `headers` | No | Custom HTTP headers |
| `params` | No | Query string parameters appended to the URL |
| `auth` | No | Basic auth tuple `[username, password]` |

### Webhook payload

When a monitor run completes, the webhook receives the same payload structure as
the `GET /catchAll/monitors/pull/{monitor_id}` response, including:

- `monitor_id` — the monitor that triggered the run
- `cron_expression` — the resolved cron schedule
- `reference_job` — the original query and context
- `run_info` — metadata about this specific run
- `records` — count of records found
- `all_records` — the clustered article data

### Delivery failures

If the webhook endpoint is unreachable or returns an error, the results are still
available via the pull endpoint. To fix webhook issues:

1. Check that the URL is publicly reachable.
2. Verify any auth headers or credentials.
3. Update the webhook config via `PATCH /catchAll/monitors/{monitor_id}`.

## Monitor lifecycle

```
Created (enabled) → Runs on schedule → Results delivered
       ↓                                       ↓
    Disabled ←──── Can be re-enabled ────→ Pull results
```

### Operations

| Action | Endpoint | Method |
|---|---|---|
| Create | `/catchAll/monitors/create` | POST |
| List all | `/catchAll/monitors/` | GET |
| Pull latest results | `/catchAll/monitors/pull/{monitor_id}` | GET |
| List run history | `/catchAll/monitors/{monitor_id}/jobs?sort=asc` | GET |
| Disable | `/catchAll/monitors/{monitor_id}/disable` | POST |
| Enable | `/catchAll/monitors/{monitor_id}/enable` | POST |
| Update webhook | `/catchAll/monitors/{monitor_id}` | PATCH |