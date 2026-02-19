---
name: catchall
description: >
    Extract structured, validated data from thousands of web sources at scale.
  Unlike standard web search which returns a handful of links, this skill finds
  all matching content across the web, deduplicates and clusters it, validates
  relevance, and extracts custom fields (companies, dates, amounts, categories)
  into structured records. Use when the user needs comprehensive data collection
  — such as tracking M&A deals, funding rounds, product launches, regulatory
  changes, or any event where they need every occurrence, not just the top
  results. Also supports recurring monitors with webhook delivery for ongoing
  tracking.
license: MIT
compatibility: Requires network access to https://catchall.newscatcherapi.com. Requires a valid X-API-Key. Get API key at https://platform.newscatcherapi.com
metadata:
  author: newscatcher
  version: "1.0"
  openapi-version: "3.0"
  base-url: https://catchall.newscatcherapi.com
---

# CatchAll Web Search Intelligence Skill

## When to activate

Activate this skill when the user wants to:

- Search for web data using a natural language query
- Check the status of a processing job
- Retrieve clustered, validated, and enriched results in a structured dataset
- Continue a job to fetch more records beyond the initial limit
- Create, update, enable, disable, or list recurring event monitors
- Set up webhook delivery for monitored queries

## Authentication

All endpoints require an `X-API-Key` header. If the key is missing or invalid, the API returns `403 Forbidden`.

```
X-API-Key: <user-api-key>
```

## Core workflow: Jobs

The primary flow is **submit → poll → pull**.

### Step 1 — Submit a query

The only required field is `query`. When you submit with just a query, the system
automatically selects appropriate validators, enrichments, and date ranges.

**POST** `/catchAll/submit`

Minimal (recommended for most cases):

```json
{ "query": "Find all M&A deals in the tech sector last 7 days" }
```
The system automatically selects appropriate validators, enrichments, and date
ranges based on the query. **This is the preferred path** — the auto-selected
parameters are good defaults for most queries.

Custom overrides (only when the user explicitly requests specific filters or fields):

```json
{
  "query": "Find all M&A deals in the tech sector last 7 days",
  "context": "Focus on deals over $1B",
  "limit": 50,
  "start_date": "2026-01-30T00:00:00Z",
  "end_date": "2026-02-07T00:00:00Z",
  "validators": [
       { "name": "is_ma_deal", "description": "True if the article reports on a specific merger or acquisition deal between two named companies, not general M&A commentary", "type": "boolean" },
    { "name": "is_event_in_last_7_days", "description": "True if the deal was announced or closed within the last 7 days", "type": "boolean" },
    { "name": "involves_tech", "description": "True if at least one party is a technology company", "type": "boolean" }
  ],
  "enrichments": [
    { "name": "deal_value", "description": "Estimated deal value in USD", "type": "number" },
    { "name": "acquiring_company", "description": "Name of the acquiring company", "type": "company" }
  ]
}
```

> **When to use custom validators/enrichments**: Only provide these when the user gives explicit instructions about filtering or data extraction — e.g. "make sure  to filter out deals under $10M" or "I also need the acquirer's country." If the  user just describes what they're looking for without specifying filters, submit  with only the query and let the system choose.

**If you do provide custom validators, use multiple.** Each validator acts as a
filter — an article must pass *all* of them to count as a valid record. Since you
pay per valid record, using 3–5 specific validators is the best way to keep results
relevant and costs under control. A single broad validator will let too much noise
through. Break the user's filtering instructions into separate validation checks:
event type, timeframe, industry, geography, significance, etc.
See `references/VALIDATORS.md` for detailed guidance.

Returns `{ "job_id": "<uuid>" }`.

**When to use `limit`**: The `limit` field is optional but important for controlling
cost and speed. Use this heuristic based on the user's intent:

| User intent | Example query | Action |
|---|---|---|
| Exhaustive / "catch all" | "Find **all** lawsuits filed against Big Tech in 2025" | Do **not** set `limit` — let the system fetch everything |
| Exploratory / general | "M&A in pharma industry in the last 30 days" | Set a `limit` (e.g. 50 to avoid over-fetching |
| Specific / narrow | "Latest news about Nvidia's earnings" | Set a low `limit` (e.g. 10) |

Look for signals like "all", "every", "complete list", "catch all", or "comprehensive"
to indicate exhaustive intent. When the query is a broad topic scan without these
signals, default to suggesting a reasonable `limit`. The user can always call
`/continue` later to expand results if the initial set isn't enough.

**Enrichment types**: `text`, `number`, `date`, `option`, `url`, `company`.

### Step 1a — Preview with Initialize (optional)

Use `/initialize` when you want to **preview** what the system would auto-select
before committing to a full run. This is useful for exploration or when the user
is unsure about the right parameters.

**POST** `/catchAll/initialize`

```json
{ "query": "AI chip export restrictions", "context": "" }
```

Returns suggested `validators`, `enrichments`, `start_date`, `end_date`.

**Intended workflow**: take the `/initialize` output, optionally adjust it (tweak
dates, add/remove enrichments, refine validators), then pass the result into
`/submit`. Think of it as a dry-run preview — it shows what *would* be configured
without actually starting a job.

> **When to skip**: If the user has a clear query and trusts the defaults, go
> straight to `/submit` with just the query. Only use `/initialize` when the user
> wants to inspect or customize parameters before running.

### Step 2 — Poll for status

**GET** `/catchAll/status/{job_id}`

Returns:

```json
{
  "job_id": "...",
  "status": "clustering",
  "steps": [
    { "status": "submitted", "order": 1, "completed": true },
    { "status": "analyzing", "order": 2, "completed": true },
    { "status": "fetching", "order": 3, "completed": true },
    { "status": "clustering", "order": 4, "completed": false },
    { "status": "enriching", "order": 5, "completed": false },
    { "status": "completed", "order": 6, "completed": false }
  ]
}
```

**Status progression**: `submitted → analyzing → fetching → clustering → enriching → completed`

**You don't need to wait for completion to see results.** The system processes
articles incrementally, so partial results are available early:

1. **After ~1–2 minutes**: call `/pull` to get the first batch of results (e.g. 14
   records may already be ready while processing continues in the background).
2. **Then poll `/status` every ~60 seconds** to track progress toward completion.
3. **Pull again** whenever you want fresher results, or wait until status is
   `completed` for the full set.

This means agents can start presenting results to the user almost immediately
while the job is still running, then refresh once it finishes.


### Step 3 — Pull results

**GET** `/catchAll/pull/{job_id}?page=1&page_size=100`

Returns clustered, validated, and enriched articles:

| Field | Description |
|---|---|
| `query` | Original query |
| `status` | Job status |
| `candidate_records` | Total articles found |
| `valid_records` | Articles passing validators |
| `all_records` | The clustered article data |
| `page` / `page_size` / `total_pages` | Pagination info |
| `duration` | Processing time |
| `date_range` | Date window of results |

## CRITICAL: Result Presentation

When presenting results to the user (regardless of interface - script, Claude Desktop, claude.ai):

**ALWAYS show the EXACT number of results returned by the API:**
- If API returns 10 records → show ALL 10
- If API returns 15 records → show ALL 15  
- If API returns 50 records → show ALL 50
- NEVER skip any records

**By default, For EACH record, display:**
- `record_title` (full title, not truncated)
- Key enrichment data (deal_value, company_name, etc.)
- At least 1 citation link with title
If a user asked to display in a custom way, obey.

**WHY this matters:**
The user set a specific limit for a reason - they want to see that EXACT number of results.
Reducing 15→12 or 20→15 breaks user expectations and wastes API quota.

**Example:**
```
User requested limit=15
API returned 15 records
You MUST show all 15 with titles, not "here are 12 highlights"
```


### Step 4 — Continue a job (optional)

If more articles are needed beyond the initial limit:

**POST** `/catchAll/continue`

```json
{ "job_id": "<uuid>", "new_limit": 200 }
```

`new_limit` must be greater than the previous limit.

### List user jobs

**GET** `/catchAll/jobs/user?page=1&page_size=100`

Returns paginated history of all jobs for the authenticated user.

## Monitors workflow

Monitors let you schedule recurring runs of a completed job's query. They are
designed for the **explore → refine → automate** pattern:

1. **Explore**: Submit a job, review the results.
2. **Refine**: Adjust validators, enrichments, date ranges — submit again until
   the output matches exactly what you need.
3. **Automate**: Once you're satisfied with the results, create a monitor using
   that job's ID as the `reference_job_id`. The monitor re-runs the same query
   with the same parameters on a schedule, and can push results to a webhook.

> **When to suggest a monitor**: If the user has iterated on a query and is happy
> with the output, proactively suggest setting up a monitor. This is especially
> valuable for data analysts who need a recurring feed — e.g. daily M&A deals,
> weekly funding rounds, or hourly breaking news on a topic.

### Create a monitor

**POST** `/catchAll/monitors/create`

```json
{
  "reference_job_id": "<uuid>",
  "schedule": "every day at 9 AM EST",
  "webhook": {
    "url": "https://your-endpoint.com/hook",
    "method": "POST",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

The `webhook` is optional. If provided it fires on each run with `url` (required), `method` (POST or PUT), `headers`, `params`, and `auth` (basic auth tuple).

### List monitors

**GET** `/catchAll/monitors/`

Returns all monitors for the user with their schedule, status, and reference query.

### Pull monitor results

**GET** `/catchAll/monitors/pull/{monitor_id}`

Returns the latest run results including `run_info`, `records`, and `all_records`.

### List monitor job history

**GET** `/catchAll/monitors/{monitor_id}/jobs?sort=asc`

Returns all jobs spawned by the monitor, sorted by `start_date`.

### Enable / Disable a monitor

**POST** `/catchAll/monitors/{monitor_id}/enable`
**POST** `/catchAll/monitors/{monitor_id}/disable`

### Update a monitor

**PATCH** `/catchAll/monitors/{monitor_id}`

```json
{
  "webhook": {
    "url": "https://new-endpoint.com/hook",
    "method": "POST"
  }
}
```

## Error handling

| Code | Meaning | Action |
|---|---|---|
| `403` | Invalid or missing `X-API-Key` | Check API key |
| `422` | Validation error | Inspect `detail[].loc` and `detail[].msg` for field-level errors |
| `200` with error status | Job failed internally | Retry with a refined query |

## Edge cases

| Scenario | Recommendation |
|---|---|
| Job stuck in `fetching` for >5 min | Re-poll; if persistent, submit a new job |
| `valid_records` is 0 | Loosen validators or broaden the query |
| Results span unexpected dates | Use explicit `start_date` / `end_date` on submit |
| Need >100 results per page | Paginate with `page` param (max `page_size` is 100) |
| Monitor webhook fails | Check URL reachability; update webhook via PATCH |

## File reference summary

| Path | Purpose |
|---|---|
| `references/OPENAPI-SPEC.json` | Full OpenAPI 3.0 spec for the CatchAll API |
| `references/ENRICHMENT-TYPES.md` | Detailed guide to enrichment types and usage |
| `references/MONITOR-SCHEDULING.md` | Cron expressions and natural language schedule examples |
| `assets/example-submit.json` | Example submit request body |
| `assets/example-pull-response.json` | Example pull response with clusters |