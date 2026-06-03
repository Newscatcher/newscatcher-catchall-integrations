# Company Watchlist Mode Reference

CatchAll's watchlist feature (`connected_dataset_ids`) scopes a query
to a list of companies. Instead of running one query per company, you
upload the list once as a dataset and run each query connected to it —
the query covers the whole list at a single query's cost. Results come
back attributed to specific companies via `connected_entities`.

This reference covers the **mechanics** only. Whether and when a skill
uses watchlist mode — and what queries it runs — is decided in that
skill's `SKILL.md`. Skills whose input is not a company list (e.g., a
regulation tracker or a sector-wide scan) ignore this file entirely;
it ships in the references package but stays inert for them.

## When a skill uses this

A skill uses watchlist mode when its input is a **list of companies** —
named in text or uploaded as a file. A single company named in text
*can* be handled by naming it directly in the query without a watchlist;
two or more should use one.

**Per-skill option — watchlist-of-1**: a skill that wants `ed_score`,
`relation`, and any cross-cutting enrichments available uniformly on
every run (regardless of competitor count) may opt to build a
watchlist-of-1 even for single-company runs. The dataset upload is one
extra round trip, but the JSON/CSV schema and downstream sections (e.g.
an "Events worth watching" filter) then work the same on every run.
competitor-snapshot uses this pattern; other skills are free not to.

## Step 1 — Build or accept the company list

The list becomes a CSV with two required columns: `name`, `domain`.

**Companies named in text** (e.g. "Atlassian, ServiceNow, Asana"):
build the CSV in memory. Fill in domains from the agent's knowledge for
well-known companies (Atlassian → `atlassian.com`). If unsure about a
specific company's domain, ask the user to confirm before uploading.

**An uploaded CSV / spreadsheet**: validate that `name` and `domain`
columns are present.
- Missing `domain` on ≤5 rows: ask the user inline for each.
- Missing `domain` on >5 rows: tell the user domain is required for
  reliable matching ("two companies can share a name, but not a
  domain") and ask them to add a domain column and re-upload.

**Why domain is required**: the CatchAll CSV upload endpoint requires
both `name` and `domain`. Domain is the most reliable matching signal;
name alone is ambiguous.

**100-entity cap**: if the list exceeds 100 rows, tell the user the
skill caps at 100, ask whether to proceed with the first 100, and
point them to the CatchAll platform + Book a demo links (see
`4-NEXT-STEPS.md`) for larger watchlists.

## Execution path: MCP, direct HTTP, or fallback

Steps 2 and 3 (upload the dataset, submit connected queries) are the
only parts of watchlist mode without a guaranteed MCP tool today.
Resolve how to run each of those two operations **at runtime** — do not
assume — in this order:

1. **MCP tool, if one exists.** If the CatchAll MCP exposes a tool for
   the operation — a dataset create/upload tool, or a submit that
   accepts a watchlist / `connected_dataset_ids` parameter — use it.
   Check the tools actually available in the run.
2. **Direct HTTP (`curl`), if the MCP has no such tool.** Requires a
   shell and a reachable API key (e.g. Claude Code with the key in
   `.env`). Endpoints and payloads are in Steps 2–3 below.
3. **Fallback, if neither is possible.** If the MCP lacks the tool *and*
   no API key is reachable for `curl` — e.g. the hosted claude.ai app,
   where the key is sealed inside the MCP connector — watchlist mode
   cannot run. Do **not** ask the user to paste an API key, and do
   **not** fan out one run per company. Skip Steps 2–3 and instead:
   - **Short list** (nameable cleanly in a query — on the order of ~10
     companies or fewer): run the skill's normal queries with **every
     company named in the query text**, one job per the skill's normal
     query — the same job count as watchlist mode, no fan-out. Add a
     `company` enrichment for attribution. This mode has no dataset
     matching, so there is no `ed_score` to threshold on — render all
     validated events, and tell the user in one line that it ran in
     named-companies mode because watchlist mode wasn't available here.
   - **Long list** (too many to name cleanly): naming dilutes retrieval
     and a per-company fan-out explodes cost — there is no good
     substitute. Tell the user the list needs watchlist mode and to run
     it in a `curl`-capable environment (e.g. Claude Code), then stop.

This is a capability check, not a fixed rule — it stays correct as the
MCP evolves. Today rung 1 usually finds no tool, so Claude Code lands
on rung 2 and the hosted app on rung 3. When the MCP gains dataset
support, rung 1 starts applying on its own and rungs 2–3 stop being
reached — **no edit to this file is needed.**

## Step 2 — Upload the list as a dataset

Run this via the execution path resolved above — the MCP dataset tool
if one exists, otherwise the direct-HTTP call below (multipart/form-data):

```
POST https://catchall.newscatcherapi.com/catchAll/datasets/upload
Content-Type: multipart/form-data
x-api-key: <key>
```

Dataset name: `<skill-slug>-<YYYYMMDD>` (the skill specifies its slug).
Capture the returned `dataset_id`.

## `ed_score` and `relation` — native scoring, no enrichment needed

Watchlist matching (`connected_dataset_ids`) is loose: it matches any
article that **mentions** a monitored company, not only articles whose
event is **about** one. So a leadership query scoped to a watchlist
containing "ServiceNow" will surface "Company X appoints an ex-ServiceNow
executive as CEO" — ServiceNow is only the person's former employer; the
event is about Company X.

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

One submit per query, each carrying `connected_dataset_ids`. Run each
via the execution path resolved above — a `submit_query` that accepts a
watchlist parameter if the MCP has one, otherwise the direct-HTTP call
below (a short inline bash loop over the `curl` submits is fine):

```
POST https://catchall.newscatcherapi.com/catchAll/submit
x-api-key: <key>
{
  "query": "<query phrased for the whole watchlist — no single company name>",
  "connected_dataset_ids": ["<dataset_id>"],
  "mode": "base",
  "limit": 100,
  "start_date": "<YYYY-MM-DD>",
  "end_date": "<YYYY-MM-DD>",
  "enrichments": [ <skill-defined enrichments only> ]
}
```

Phrase the query for the whole list ("…by companies in this
watchlist…") rather than naming any one company — the
`connected_dataset_ids` parameter does the scoping. The `enrichments`
array carries only the skill's own domain fields — `ed_score` and
`relation` arrive natively on `connected_entities`, no enrichment needed.

Capture each `job_id`. Submit in concurrency-sized waves (see
`2-JOB-LIFECYCLE.md` § Concurrency).

## Step 4 — Poll, pull, attribute, split

Polling and pulling use the MCP tools normally —
`mcp__catchall__get_job_status` and `mcp__catchall__pull_results` only
need the `job_id`, so they work regardless of how the job was submitted.

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

The `8` cut is calibrated, not arbitrary: on a 164-record test run
`ed_score` was sharply bimodal — events genuinely about the company at
8–10, passing mentions concentrated at 1–7 (every score-5 record, and
9 of 10 score-7 records, were passing mentions). Records cluster away
from the boundary, so the threshold is stable.

Keep `ed_score` and `relation` on every event in the JSON / CSV: the
full dataset stays complete and verifiable, and `relation` tells a
spreadsheet reader why each company matched. Neither field — nor any
mention of the scoring — appears in the chat: the reader simply sees
the surfaced events and an `([n] more in the full dataset)` line.

## Do not write a helper script

Every step above is a single `curl`, a single MCP call, or a short
inline bash loop. Do not wrap the orchestration in a `.py` script —
see `2-JOB-LIFECYCLE.md` § No helper scripts.
