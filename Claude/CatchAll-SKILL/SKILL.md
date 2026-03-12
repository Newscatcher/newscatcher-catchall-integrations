---
name: catchall
description: >
  Extract structured, validated data from thousands of web sources at scale using
  the CatchAll API. Use this skill whenever the user wants to search for, track,
  or monitor structured information from news and the web — M&A deals, funding
  rounds, product launches, regulatory changes, executive moves, market events, or
  any recurring topic they want to watch over time. Trigger this skill even when
  the user doesn't say "CatchAll" explicitly — if they say things like "find all
  acquisitions in pharma this week", "track Series A rounds", "monitor news about
  X", "set up a recurring alert", "pull structured data from news", or "how many
  deals happened in Y sector", this skill applies. Unlike web search (which returns
  a handful of links), CatchAll scans thousands of sources, validates relevance,
  deduplicates, and returns structured records with extracted fields. Also handles
  recurring monitors with webhook delivery.
license: MIT
compatibility: Requires network access to https://catchall.newscatcherapi.com. Requires a valid X-API-Key passed by the user or found in the environment as CATCHALL_API_KEY.
metadata:
  author: newscatcher
  version: "1.1"
  base-url: https://catchall.newscatcherapi.com
---

# CatchAll Web Search Intelligence Skill

## Authentication

All endpoints require an `X-API-Key` header. Before making any call:

1. Check if `CATCHALL_API_KEY` is set in the environment.
2. If not, ask the user: "Please provide your CatchAll API key."

Never proceed without a key — the API returns `403 Forbidden` and the job won't start.

---

## Core workflow: submit → poll → pull

### Step 1 — Submit a query

**POST** `https://catchall.newscatcherapi.com/catchAll/submit`

The only required field is `query`. Submit with just the query by default — the system auto-selects validators, enrichments, and date range. This is the preferred path.

```bash
curl -X POST https://catchall.newscatcherapi.com/catchAll/submit \
  -H "X-API-Key: $CATCHALL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all M&A deals in the tech sector last 7 days"}'
# Returns: {"job_id": "<uuid>"}
```

**When to set a `limit`:**

| User intent | Signal words | Action |
|---|---|---|
| Exhaustive | "all", "every", "complete list", "catch all" | No limit |
| Exploratory | broad topic, no signal words | Set `limit: 50` |
| Specific/narrow | one company, one event | Set `limit: 10` |

**Custom validators/enrichments** — only provide these when the user explicitly asks for specific filters or fields. Otherwise let the system choose. See `references/VALIDATORS.md` and `references/ENRICHMENT-TYPES.md` for schemas and examples.

**Optional: preview with `/initialize`**

Use `POST /catchAll/initialize` with `{"query": "..."}` to see what the system would auto-select (validators, enrichments, date range) before committing. Useful when the user wants to inspect or tweak parameters first.

---

### Step 2 — Poll for status

**GET** `https://catchall.newscatcherapi.com/catchAll/status/{job_id}`

Status progression: `submitted → analyzing → fetching → clustering → enriching → completed`

**You don't need to wait for completion.** Pull partial results after ~1–2 minutes while the job is still running, then poll every ~60 seconds. This lets you show results to the user almost immediately.

---

### Step 3 — Pull results

**GET** `https://catchall.newscatcherapi.com/catchAll/pull/{job_id}?page=1&page_size=100`

```bash
curl "https://catchall.newscatcherapi.com/catchAll/pull/$JOB_ID?page=1&page_size=100" \
  -H "X-API-Key: $CATCHALL_API_KEY"
```

**Key response fields:**

| Field | Description |
|---|---|
| `all_records` | ⚠️ The actual data — array of clustered, validated articles |
| `valid_records` | Count of articles that passed validators (not the data itself) |
| `candidate_records` | Total articles examined |
| `total_pages` | Use with `page` param if paginating |

> **Common mistake**: `valid_records` is just a count. The actual records are in `all_records`.

**Per-record structure:**

```json
{
  "record_id": "...",
  "record_title": "...",
  "enrichment": { ... },   // ← singular "enrichment", not "enrichments"
  "citations": [ { "title": "...", "link": "...", "published_date": "..." } ]
}
```

> ⚠️ **Critical**: The extracted fields are in `enrichment` (singular), not `enrichments`. Accessing `.enrichments` will return `undefined`/`null`.

---

## Presenting results

**Always show the exact number of records returned.** Never summarize down to fewer.

For each record, display:
- `record_title` (full, not truncated)
- Key fields from `enrichment` (e.g. deal_value, acquiring_company, round_type)
- At least one citation link

```
# Example display for a single record:
**GSK Acquires RAPT Therapeutics**
- Deal value: $2.2B | Type: Acquisition | Status: Announced
- Acquiring: GSK plc → Acquired: RAPT Therapeutics
- Source: [GSK Strengthens Immunology Pipeline](https://...)
```

---

### Step 4 — Continue a job (optional)

If the user needs more records beyond the initial limit:

```bash
curl -X POST https://catchall.newscatcherapi.com/catchAll/continue \
  -H "X-API-Key: $CATCHALL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "<uuid>", "new_limit": 200}'
```

`new_limit` must be greater than the previous limit.

---

### List user jobs

**GET** `/catchAll/jobs/user?page=1&page_size=100` — paginated history of all jobs.

---

## Monitors workflow

Monitors schedule recurring runs of a completed job's query. Use the **explore → refine → automate** pattern:

1. Submit and iterate until the results match what the user wants.
2. Once satisfied, create a monitor using that job's `job_id` as `reference_job_id`.

> Proactively suggest monitors when the user has a query they're happy with and the topic recurs over time (e.g. weekly M&A, daily funding rounds, hourly news on a topic).

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

`webhook` is optional. If omitted, results are available via pull. See `references/MONITOR-SCHEDULING.md` for schedule format and examples.

### Monitor operations

| Action | Endpoint | Method |
|---|---|---|
| List all | `GET /catchAll/monitors/` | — |
| Pull latest results | `GET /catchAll/monitors/pull/{monitor_id}` | — |
| List run history | `GET /catchAll/monitors/{monitor_id}/jobs?sort=asc` | — |
| Disable | `POST /catchAll/monitors/{monitor_id}/disable` | — |
| Enable | `POST /catchAll/monitors/{monitor_id}/enable` | — |
| Update webhook | `PATCH /catchAll/monitors/{monitor_id}` | `{"webhook": {...}}` |

---

## Error handling

| Code | Meaning | Action |
|---|---|---|
| `403` | Invalid or missing API key | Ask user for their key |
| `422` | Validation error | Inspect `detail[].loc` and `detail[].msg` |
| `200` with error status | Job failed internally | Retry with a refined query |

**Edge cases:**

| Scenario | Recommendation |
|---|---|
| `valid_records` is 0 | Loosen validators or broaden the query |
| Job stuck in `fetching` >5 min | Re-poll; if persistent, submit a new job |
| Results span unexpected dates | Use explicit `start_date` / `end_date` on submit |
| Need >100 results per page | Paginate with `page` param (max `page_size` is 100) |
| Monitor webhook fails | Check URL reachability; update via PATCH |

---

## Reference files

| Path | When to read |
|---|---|
| `references/VALIDATORS.md` | User wants custom validators or asks about filtering logic |
| `references/ENRICHMENT-TYPES.md` | User wants custom enrichment fields or asks about extraction types |
| `references/MONITOR-SCHEDULING.md` | User wants to set up a monitor or asks about scheduling |
| `references/openapi-spec.json` | Full API spec — consult for edge cases or unlisted params |
| `assets/example-submit.json` | Example submit payload |
| `assets/example_pull_response.json` | Example pull response with real record structure |