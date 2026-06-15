# Company Watchlist Mode Reference

CatchAll's watchlist feature scopes a query to a list of companies.
Instead of running one query per company, you build the list once as a
dataset (a set of company entities) and run each query connected to it —
the query covers the whole list at a single query's cost. Results come
back attributed to specific companies via `connected_entities`.

## When a skill uses this

A skill uses watchlist mode when its input is a **list of companies** —
named in text or uploaded as a file. A single company named in text
*can* be handled by naming it directly in the query without a watchlist;
two or more should use one.

**Per-skill option — watchlist-of-1**: a skill that wants `ed_score`,
`relation`, and any cross-cutting enrichments available uniformly on
every run (regardless of competitor count) may opt to build a
watchlist-of-1 even for single-company runs. Building the dataset is one
extra round trip, but the JSON/CSV schema and downstream sections (e.g.
an "Events worth watching" filter) then work the same on every run.

## Step 1 — Build or accept the company list

The list resolves to two required fields per company: `name`, `domain`.

**Companies named in text** (e.g. "Atlassian, ServiceNow, Asana"):
build the list in memory. Fill in domains from the agent's knowledge for
well-known companies (Atlassian → `atlassian.com`). If unsure about a
specific company's domain, ask the user to confirm before building.

**An uploaded CSV / spreadsheet**: the user can still hand over a CSV —
validate that `name` and `domain` columns are present.
- Missing `domain` on ≤5 rows: ask the user inline for each.
- Missing `domain` on >5 rows: tell the user domain is required for
  reliable matching ("two companies can share a name, but not a
  domain") and ask them to add a domain column and re-upload.

**Why domain is required**: CatchAll entities are keyed on `name` +
`domain`. Domain is the most reliable matching signal; name alone is
ambiguous.

**100-entity cap**: if the list exceeds 100 companies, tell the user the
skill caps at 100, ask whether to proceed with the first 100, and
point them to the CatchAll platform + Book a demo links (see
`NEXT-STEPS.md`) for larger watchlists.

## Execution path: build and query the watchlist through the MCP

Watchlist mode runs **entirely through the CatchAll MCP** — two
operations: build the dataset from the company list (Step 2) and submit
queries connected to it (Step 3). Both have MCP tools, so watchlist mode
works on **every platform with the CatchAll MCP connected** — the hosted
claude.ai app and ChatGPT included, not just Claude Code. There is no
curl path and no API key to handle.

> **Tool prefix varies by host.** The tools below are CatchAll MCP
> operations (`create_entities_batch`, `create_dataset`, `submit_query`,
> …). The server-name prefix differs per environment — `mcp__catchall__…`
> in some Claude Code configs, `mcp__claude_ai_CatchAll__…` on claude.ai.
> Detect and call whatever prefix this run exposes; never hardcode one.

**Pre-flight capability check (inspect, don't assume):** list the
available CatchAll MCP tools (match on the operation name, ignoring the
server prefix) and check for the entity/dataset tools — `create_entities_batch`
and `create_dataset`.

- **Present** → run Steps 2–4 over the MCP. The normal path.
- **Absent** (an older CatchAll MCP without watchlist tools) → degrade
  gracefully, never error:
  - **Short list** (~10 companies or fewer): run the skill's normal
    queries with **every company named in the query text** — one job per
    query, same job count, no fan-out. Add a `company` enrichment for
    attribution. No dataset matching means no `ed_score`, so render all
    validated events and tell the user in one line it ran in
    named-companies mode.
  - **Long list**: tell the user watchlist mode needs the updated
    CatchAll MCP and to update it, then stop. Do **not** fan out one run
    per company (it explodes cost) and do **not** ask for an API key.

## Step 2 — Build the dataset from the company list

The list is **not** uploaded as a file. Build it from entities, two MCP calls:

1. **Batch-create the company entities** — `create_entities_batch`, one
   object per company. The domain lives under `company_attributes`:

   ```
   create_entities_batch(entities=[
     {"name": "<company>", "entity_type": "company",
      "additional_attributes": {"company_attributes": {"domain": "<domain>"}}},
     ...
   ])
   ```
   One call for the whole list — do **not** loop `create_entity` per
   company. Capture the returned entity IDs.

2. **Create the dataset, seeded with those entities** —
   `create_dataset(name="<skill-slug>-<YYYYMMDD>", entity_ids=[<IDs from step 1>])`.
   Capture the returned `dataset_id`. (`entity_ids` seeds it in the same
   call; `add_dataset_entities` is only for adding more later.)

**Dataset readiness:** a dataset may enrich asynchronously after creation
(`get_dataset_status` shows its progress). If connected queries come back
empty immediately after creation, poll `get_dataset_status` until ready,
then resubmit.

## `ed_score` and `relation` — native scoring, no enrichment needed

Watchlist matching is loose: it matches any article that **mentions** a
monitored company, not only articles whose event is **about** one. So a
leadership query scoped to a watchlist containing "ServiceNow" will
surface "Company X appoints an ex-ServiceNow executive as CEO" —
ServiceNow is only the person's former employer; the event is about
Company X.

CatchAll already scores exactly this. Every element of
`connected_entities` (the matched-company list on each result) carries
two **native** fields — they come back automatically; you do **not**
request them as enrichments:

| Field | Type | Meaning |
|---|---|---|
| `ed_score` | integer 1–10 | How central the company is to the event. High = the event is about this company; low = a passing mention. |
| `relation` | string | One-line description of how the company connects to the event — the human-readable "why it matched". |

```json
"connected_entities": [
  {
    "entity_id": "86d09fcf-21b1-4cf3-90c2-979f97f54981",
    "name": "Western Digital Corporation",
    "type": "company",
    "ed_score": 10,
    "relation": "Directly discusses Western Digital's HDD capacity roadmap and AI-driven demand.",
    "company": { "domain": "westerndigital.com" }
  }
]
```

Because `ed_score` is native, watchlist queries need **no extra
enrichment** to separate central events from passing mentions — the
skill's `enrichments` array holds only its own domain fields. Do **not** add a `connection_type`
(or similar) enrichment: `ed_score` replaces it and is more reliable,
since it is computed by CatchAll's matching pipeline rather than
re-derived by an enrichment LLM.

## Step 3 — Submit queries connected to the dataset

One submit per query via `submit_query`, each connected to the dataset:

```
submit_query(
  query = "<query phrased for the whole watchlist — no single company name>",
  connected_dataset_ids = ["<dataset_id>"],
  mode  = "base",
  limit = 100,
  start_date = "<YYYY-MM-DD>", end_date = "<YYYY-MM-DD>",
  enrichments = [ <skill-defined enrichments only> ],
)
```

`connected_dataset_ids` does the scoping — phrase the query for the whole
list ("…by companies in this watchlist…"), never naming one company. The
`enrichments` array carries only the skill's own domain fields; `ed_score`
and `relation` arrive natively on `connected_entities`, no enrichment needed.

**`ed_score_min`:** when `connected_dataset_ids` is set, the API defaults
`ed_score_min` to 2 (drops only score-1 noise). **Leave it at the
default** — this skill keeps the full range in the JSON/CSV and applies the
`ed_score >= 8` chat cut locally (Step 4). Raising it server-side would drop
the lower-scored records the full dataset is meant to retain. (Pass
`ed_score_min=1` if you want score-1 records in the files too.)

Capture each `job_id`. Submit in concurrency-sized waves (see
`CONCURRENCY.md`).

## Step 4 — Poll, pull, attribute, split

Polling and pulling use the MCP tools normally — `get_job_status` and
`pull_results` only need the `job_id`.

**Attribution**: each pulled event has a `connected_entities` list —
one element per matched watchlist company, each with its own `ed_score`.
Attribute the event to its **highest-`ed_score`** company and use that
name for the per-company attribution column.

**What goes in the chat vs the files** — threshold on the attributed
company's `ed_score`:
- `ed_score >= 8` → surfaced in the chat output (and in the downloads),
  and counts toward the headline "events found".
- `ed_score < 8` → a passing mention. Goes **only** into the JSON / CSV
  downloads, never into the chat tables, and is **not** counted in the
  headline total.

Keep `ed_score` and `relation` on every event in the JSON / CSV: the
full dataset stays complete and verifiable, and `relation` tells a
spreadsheet reader why each company matched. Neither field — nor any
mention of the scoring — appears in the chat: the reader simply sees
the surfaced events and an `([n] more in the full dataset)` line.

## Do not write a helper script

Every step above is a single MCP call (or a short batch call). Do not
wrap the orchestration in a `.py` script — call the tools directly.
Orchestration scripts cause debug-retry cycles and stale intermediate
state; a short inline loop over repeated MCP calls is fine.
