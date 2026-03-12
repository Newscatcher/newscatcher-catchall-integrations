# Monitor Scheduling Reference

Monitors run a completed job's query on a recurring schedule.

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

`reference_job_id` must point to a completed job. The monitor re-uses that job's
query, validators, enrichments, and parameters for every run.

## Schedule format

Use natural language with a timezone. The system converts to cron internally.

| Schedule | Meaning |
|---|---|
| `"every day at 9 AM EST"` | Daily at 9:00 AM Eastern |
| `"every Monday at 8 AM UTC"` | Weekly on Mondays |
| `"every 6 hours"` | Every 6 hours from creation |
| `"every weekday at 7 AM PST"` | Monday–Friday at 7:00 AM Pacific |
| `"twice a day at 8 AM and 6 PM EST"` | Twice daily |
| `"every first Monday of the month at 9 AM UTC"` | Monthly |

Always include a timezone. For news monitoring, daily or twice-daily works best.

## Webhook configuration

Optional. If omitted, results are available via `GET /catchAll/monitors/pull/{monitor_id}`.

```json
{
  "url": "https://your-endpoint.com/hook",
  "method": "POST",
  "headers": { "Authorization": "Bearer your-token", "Content-Type": "application/json" },
  "params": { "source": "catchall" },
  "auth": ["username", "password"]
}
```

| Field | Required | Description |
|---|---|---|
| `url` | Yes | Destination URL |
| `method` | No | `POST` (default) or `PUT` |
| `headers` | No | Custom HTTP headers |
| `params` | No | Query string parameters |
| `auth` | No | Basic auth tuple `[username, password]` |

If the webhook fails, results are still available via the pull endpoint.
Fix via `PATCH /catchAll/monitors/{monitor_id}`.

## Monitor lifecycle

```
Created (enabled) → Runs on schedule → Results delivered via webhook or pull
       ↓
    Disabled ←── Can be re-enabled
```