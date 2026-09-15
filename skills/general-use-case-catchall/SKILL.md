---
name: general-use-case-catchall
description: >
  Use this skill whenever the user wants to search for events or facts across
  the web, set up a recurring monitor, configure a webhook, build a watchlist
  of companies or people, or organize work into projects — even if they don't
  say "CatchAll" explicitly. Triggers on phrases like "find all X in the last
  N days", "monitor this query weekly", "alert me when Y happens", "track these
  companies", "set up a Slack notification for Z", "how many credits do I have
  left", or any request to manage past jobs or monitors. Extracts structured,
  validated data from thousands of web sources — deduplicates, clusters,
  validates relevance, and extracts custom fields into structured records. Covers
  the full CatchAll platform surface: jobs, monitors, webhooks, datasets,
  entities, and projects. Use dedicated skills (fundraising-catchall,
  mergers-and-acquisitions-catchall, competitor-snapshot-catchall) for those
  specific event types when the user's intent clearly matches — but when in
  doubt, use this skill.
license: MIT
compatibility: Requires the CatchAll MCP server at https://catchall-mcp.newscatcherapi.com/mcp. Requires a valid CatchAll API key. Get one at https://platform.newscatcherapi.com
metadata:
  author: newscatcher
  version: "2.0"
---

## MANDATORY: Read this skill before answering ANY question about CatchAll

Do not answer from memory. Every answer about entities, datasets, jobs, monitors,
or webhooks must be grounded in this skill. If a section seems relevant, read it
before responding. Prior knowledge about CatchAll is likely incomplete or outdated
— always defer to what is written here.

---

This skill covers the full CatchAll surface: how to write queries that produce
results, which tool to call for each task, and how to use the platform's
organizational features (webhooks, datasets, entities, projects). The MCP
server handles authentication, routing, and response schemas — this skill
handles judgment.

---

## CRITICAL: Never query for web pages

Before constructing any query, run this self-check:

**Does my query contain any of these forbidden phrases?**

- `news articles`, `news stories`, `articles about`, `stories about`
- `press coverage`, `media coverage`, `recent news`
- `find articles`, `search articles`, `get articles`, `coverage of`

If yes — **stop and rewrite**. CatchAll's pipeline interprets the query as a
description of a real-world event to find. A journalism-style query ("articles
about X") confuses its intent classifier, which then retrieves coverage of a
topic rather than occurrences of an event — producing off-target or empty
results even when the underlying events clearly exist in the index.

**Wrong:** `"news articles about AI regulation in the EU last 30 days"`
**Right:** `"AI regulation measures announced or enacted in the EU in the last 30 days"`

**Wrong:** `"find articles covering product launches by Apple"`
**Right:** `"product launches announced by Apple in the last 14 days"`

This distinction applies to validators and enrichments too. Never write a
validator like `"article mentions a product launch"` — write
`"a company has officially announced a new product or feature"`.

---

## How to build a query

Write a natural language sentence that describes the real-world event or fact
you are looking for. CatchAll processes natural language — do not reduce it to
keyword strings.

**Formula: describe what happened + 2–4 specifics**

| Specifics | Notes |
|---|---|
| **Event type** | What occurred — acquisition, product launch, regulatory fine, leadership change, etc. |
| **Entity** | Company, person, geography, or industry involved — only if specified by the user |
| **Timeframe** | Explicit window within 30 days ("last 14 days"); never open-ended ("since January") |
| **Location** | City, region, country, or global; omit if not specified |

**Examples:**

| User input | Query to build |
|---|---|
| "EU fines on Big Tech last month" | `"fines or penalties imposed on Big Tech companies by EU regulators in the last 30 days"` |
| "new AI models released this week" | `"AI models or AI systems officially launched or released in the last 7 days"` |
| "executive departures at banks" | ask for timeframe, then: `"CEO or C-suite departures at major banks announced in the last 30 days"` |
| "supply chain disruptions in semiconductors" | `"supply chain disruptions or shortages affecting semiconductor companies in the last 14 days"` |

**Constraint limit:** Cap at 4 meaningful constraints. More than that and results
will silently return nothing — CatchAll can't match a 6-way intersection that
rarely appears in a single source.

If the user has not provided a timeframe, ask before submitting.

**Timeframe window:** Max 30 days per query. For longer requests, split into
consecutive 30-day windows and run each as a separate job.

---

## Before you submit: validate_query

Run `validate_query` when the user's query is ambiguous, very broad, or likely
to be misinterpreted. It checks query quality without creating a job or spending
credits.

Returns `status`:
- `good` — submit as-is
- `needs_work` — review `issues` and `suggestions` before submitting
- `critical` — rewrite before submitting; the query will likely return nothing useful

**When to use it:**

- Query is vague ("tell me about Tesla")
- Query mixes event descriptions with page-description language
- You are unsure whether the query is too constrained or too broad

**When to skip it:** The user has a clear, well-formed event query — go straight
to `submit_query`.

---

## Tool reference

### Jobs

| Task | Tool |
|---|---|
| Check query quality before submitting | `validate_query` |
| Preview auto-selected validators/enrichments/dates | `initialize_query` |
| Submit a query and start a job | `submit_query` |
| Check job processing status | `get_job_status` |
| Retrieve results (partial or complete) as JSON | `pull_results` |
| Download completed job results as a CSV file | `pull_job_csv` |
| Fetch more records beyond the initial limit | `continue_job` |
| List past jobs | `list_user_jobs` |
| Delete a job and its results | `delete_job` |

**Polling cadence:** call `pull_results` after ~1–2 minutes — results are
available incrementally before the job completes. Then poll `get_job_status`
every ~60 seconds to track completion.

**Status progression:** `submitted → analyzing → fetching → clustering → enriching → completed`

**CSV vs. JSON:** Use `pull_job_csv` when the consumer needs a spreadsheet or
CSV file. Use `pull_results` when you need paginated JSON (e.g., to display
results inline or pass them to a downstream tool that expects structured JSON).
`pull_job_csv` requires the job to be in `completed` status.

**`list_user_jobs` filters:** In addition to `page`/`page_size`, `list_user_jobs`
accepts `search` (text filter on the job query), `ownership` (`all`, `own`, or
`shared`), `project_id` (filter to a specific project), and `mode` (`base` or
`lite`). Use `mode` when you want to list only jobs submitted in a specific
processing mode — for example, to audit which jobs ran in `lite` mode or to
separate cost-optimised runs from full-enrichment runs.

### Monitors

| Task | Tool |
|---|---|
| Create a recurring scheduled job | `create_monitor` |
| List all active monitors | `list_monitors` |
| Get latest run output as JSON | `pull_monitor_results` |
| Download latest run results as a CSV file | `pull_monitor_csv` |
| See all runs for a monitor | `list_monitor_jobs` |
| See monitor state change history | `get_monitor_status` |
| Pause a monitor | `disable_monitor` |
| Resume a paused monitor | `enable_monitor` |
| Change webhook or per-run limit | `update_monitor` |
| Delete a monitor permanently | `delete_monitor` |

**CSV vs. JSON for monitors:** Use `pull_monitor_csv` when the user wants to
download the most recent monitor run as a spreadsheet. Use `pull_monitor_results`
for inline JSON inspection or downstream processing.

### Webhooks

| Task | Tool |
|---|---|
| Create a webhook endpoint | `create_webhook` |
| List all webhooks | `list_webhooks` |
| Get full webhook config | `get_webhook` |
| Update webhook settings | `update_webhook` |
| Test a webhook before attaching it | `test_webhook` |
| Attach a webhook to a job or monitor | `assign_webhook_resource` |
| List webhooks on a resource | `list_resource_webhooks` |
| List resources attached to a webhook | `list_webhook_resources` |
| Remove a webhook from a resource | `remove_webhook_resource` |
| View delivery history | `get_webhook_history` |
| Manually trigger webhook delivery for a resource | `trigger_webhook` |
| Delete a webhook | `delete_webhook` |

**`create_webhook` — project association:** Pass the optional `project_id`
parameter to attach the webhook to a project immediately on creation. This is
equivalent to calling `add_project_resources` afterwards with
`resource_type="webhook"`, but saves a round-trip. A webhook can belong to
several projects at once; use `add_project_resources` to attach it to
additional projects later.

**`list_webhooks` — project filter:** Pass the optional `project_id` parameter
to filter the listing to only webhooks belonging to a specific project. This
mirrors the same filter available on `list_user_jobs`, `list_monitors`, and
`list_datasets`.

**`trigger_webhook` — manual delivery:** Use `trigger_webhook` when you need to
(re-)send a webhook delivery on demand — for example, to replay a missed or
failed delivery without waiting for the next scheduled run. Required params:
`webhook_id`, `resource_type` (`job`, `monitor`, or `monitor_group`), and
`resource_id`. The optional `job_id` param specifies which run's payload to
deliver (e.g., a specific monitor run); if omitted, the API picks the
resource's own payload. The dispatch is **asynchronous** — `trigger_webhook`
returns `{"success": true, "message": "Webhook trigger dispatched."}` immediately.
Always follow up with `get_webhook_history` to confirm the delivery outcome.

**`get_webhook_history` — two query modes:** Call this tool in exactly one of
two modes per call — mixing parameters from both modes raises a validation error:

| Mode | Parameters to pass | What you get |
|---|---|---|
| **Resource mode** | `resource_type` + `resource_id` | All deliveries made for a specific job, monitor, or monitor_group |
| **Webhook mode** | `webhook_id` | Every delivery made through one webhook, across all resources |

Webhook mode is the **only** place manual test deliveries (from `test_webhook`)
appear — they are recorded with `resource_type: "test"` and are not tied to any
job or monitor. Use webhook mode when diagnosing a specific endpoint's delivery
history or auditing test calls. Use resource mode when diagnosing why a specific
job or monitor did or did not deliver.

### Datasets & Entities

| Task | Tool |
|---|---|
| Create a single entity (company or person) | `create_entity` |
| Create multiple entities at once | `create_entities_batch` |
| Get / update / delete an entity | `get_entity` / `update_entity` / `delete_entity` |
| List all entities | `list_entities` |
| Create a dataset (named collection of entities) | `create_dataset` |
| Create a dataset by uploading CSV content | `create_dataset_from_csv` |
| Append CSV content to an existing dataset | `append_csv_to_dataset` |
| Add / remove entities from a dataset | `add_dataset_entities` / `remove_dataset_entities` |
| List entities in a dataset | `list_dataset_entities` |
| Get dataset enrichment status | `get_dataset_status` |
| List all datasets | `list_datasets` |
| Delete a dataset (entities are preserved) | `delete_dataset` |

**`list_entities` — project filter:** Pass the optional `project_id` parameter
to filter the listing to only entities belonging to a specific project. This
mirrors the same filter available on `list_user_jobs`, `list_monitors`,
`list_datasets`, and `list_webhooks`.

### Source Groups

| Task | Tool |
|---|---|
| List available named source-domain allowlists | `list_source_groups` |

**Source groups** are reusable, named sets of source domains maintained by
NewsCatcher. `list_source_groups` returns public groups plus any
organization-visibility groups your organization can access. Each item has a
`slug`, `name`, and `description`. Supports optional `page`/`page_size`
pagination (max `page_size`: 500).

Use `list_source_groups` when the user wants to scope a query to a specific set
of domains (e.g., only tier-1 financial outlets, only government sources). Once
you have the group's `slug`, pass it via the `source_groups` field on the direct
`POST /catchAll/submit` API call. **Note:** `submit_query` (the MCP tool) does
not yet expose a `source_groups` parameter — use the direct API for this until
a future release adds it.

### Projects

| Task | Tool |
|---|---|
| Create a project | `create_project` |
| List all projects | `list_projects` |
| Get resource summary for a project | `get_project_overview` |
| Add jobs / monitors / datasets / webhooks to a project | `add_project_resources` |
| List resources inside a project | `list_project_resources` |
| Remove a resource from a project | `remove_project_resource` |
| Update or delete a project | `update_project` / `delete_project` |

**Project `resource_type` values:** `job`, `monitor`, `dataset`, `monitor_group`,
or `webhook`. Webhooks are first-class project resources — a webhook can belong
to several projects at once. When you call `add_project_resources`,
`list_project_resources`, or `remove_project_resource`, pass
`resource_type="webhook"` to manage webhook membership.

**`delete_project` and webhooks:** Deleting a project (with or without
`delete_resources=true`) **never deletes webhooks** — it only detaches them.
The response's `deleted_resources` map includes a `webhook_unlinked` count
showing how many webhooks were detached. Detached webhooks continue to exist
and remain attached to any other projects or resources they belong to.

### Utilities

| Task | Tool |
|---|---|
| Check credit usage and plan limits | `get_user_limits` |
| Check API health | `check_health` |

---

## Error handling

All tools raise a real MCP tool error (`isError=True`) for any upstream non-2xx
response (bad `api_key`, invalid or foreign `project_id`, not-found IDs,
validation failures, etc.) or unhandled exception. The error message carries the
upstream status code and message — for example, `API Error (401): Api key not
found`. **Do not** rely on parsing the result text for `"Error: ..."` strings —
check `isError` on the tool call result.

Legitimate 2xx responses with an empty body (e.g., a 204 delete, or a
zero-result list) are **not** errors — that path is unaffected.

---

## Job modes

Pass `mode` in `submit_query`:

| Mode | Speed | Cost | Enrichments | Use when |
|---|---|---|---|---|
| `base` (default) | Standard | Standard | Full enrichment pipeline | User needs structured data fields, deduplication, clustering |
| `lite` | Faster | Lower | Validators only, no enrichment metadata | User needs fast filtering with no structured extraction |

Use `lite` when the user just wants to know if something happened and doesn't
need specific fields extracted. Use `base` for any structured output.

The same `base`/`lite` values are accepted by `list_user_jobs` as a `mode`
filter to narrow the listing to jobs that ran in a specific processing mode.

---

## Limit vs. page_size — critical distinction

| Parameter | Where | Cost impact | Purpose |
|---|---|---|---|
| `limit` | `submit_query`, `continue_job`, `update_monitor` | **Yes — affects billing** | How many records to process and validate |
| `page_size` | `pull_results`, list tools | **No — free** | How many records to return per API response |

**Never use `page_size` to control how much data is processed.** Use `page_size`
only for pagination of results already processed by a job. The `limit` is the
lever that controls both scope and cost.

**`limit` minimum:** If `limit` is provided, it must be `>= 10`. Omit `limit`
entirely to retrieve everything up to your plan's maximum.

### Limit heuristics

| User intent | Signal words | Action |
|---|---|---|
| Exhaustive | "all", "every", "complete list", "catch all" | Omit `limit` |
| Exploratory | general topic scan, no quantity stated | `limit: 50` |
| Specific / narrow | single entity, single event, "latest" | `limit: 10` |

The user can always call `continue_job` later to expand beyond the initial limit.

---

## Validators

Validators are boolean filters. An article must pass **all** of them to count
as a valid (billed) record. When the user submits with just a query, CatchAll
auto-selects validators — this is the preferred path for most cases.

Specify custom validators only when the user gives explicit filtering
instructions ("exclude rumors", "only confirmed deals", "must mention a dollar
amount"). When you do:

- Use 3–5 validators, not just one — a single broad validator lets noise through
- Break filtering intent into separate checks: event type, timeframe, geography, significance
- Write descriptions as event-scoped assertions, not page descriptions

See `references/VALIDATORS.md` for detailed guidance and examples.

---

## Enrichments

Enrichments are structured fields extracted from each valid result. Enrichment
types: `text`, `number`, `date`, `option`, `url`, `company`.

**When to specify enrichments:** user needs a structured table, a CSV export, or
specific named fields (deal value, company name, announcement date).

**When to skip:** user asks for a free-form summary or "just tell me what
happened" — let the agent interpret result text directly without pre-defined fields.

When you define enrichments, be explicit about the field names so they stay
stable across runs. Unstable field names break downstream formatting.

---

## Datasets & Entities: watchlist mode

Use datasets when the user wants to track a specific list of companies or people
rather than a broad topic. This is "watchlist mode" — results are attributed back
to named entities in the list.

**Workflow:**

1. Create entities with `create_entity` or `create_entities_batch` (type: `company` or `person`)
2. Create a dataset with `create_dataset` and add entities to it
3. Wait for dataset status to reach `ready` — entities are enriched before first use
4. Pass `connected_dataset_ids: [<dataset_id>]` in `submit_query`

**Entity fields:**

| Field | Required | Notes |
|---|---|---|
| `name` | Yes | Full legal or widely-recognised company name |
| `description` | One of `description` or `domain` is required | See guidance below |
| `additional_attributes.company_attributes.domain` | One of `description` or `domain` is required | Company website, e.g. `"acme.com"` |
| `entity_type` | No | `"company"` or `"person"` |
| `external_entity_id` | No | Your own internal ID — see below |
| `additional_attributes.company_attributes.alternative_names` | No | Other names the company is known by |
| `additional_attributes.company_attributes.key_persons` | No | Notable executives or founders |

**What makes a strong description:**

Descriptions must **fingerprint the company, not market it**. The enrichment pipeline uses the description to correctly identify and disambiguate the entity in news coverage — a vague description causes missed or incorrect matches.

A good description spans two to four sentences covering:
- Full legal name and specific industry sector
- Headquarters location and operating regions
- Founding year and founders
- Concrete products or services offered

Drop generic adjectives ("leading", "innovative", "world-class") — they carry no disambiguating signal and waste space.

**Wrong:** `"A leading provider of innovative cloud solutions."`
**Right:** `"Acme Corp is a B2B SaaS company founded in 2015 in San Francisco, offering sales intelligence and lead-enrichment software to mid-market and enterprise sales teams in North America and Europe."`

**`external_entity_id` — linking entities to external systems:**

Both `create_entity` and `update_entity` accept an optional `external_entity_id`
string. Set this when entities correspond to records in an external system (e.g.,
a CRM, data warehouse, or internal database). The value is a customer-supplied
identifier that CatchAll stores alongside the entity for traceability. Always set
it at creation time if you have a stable external ID — it is much harder to
reconcile after the fact.

Example: `"external_entity_id": "crm-account-00123"`

**`ed_score_min` — entity confidence threshold:**

When using a dataset, each result is scored against how confidently it matches
an entity in the list (`ed_score` 0–10). Pass `ed_score_min` in `submit_query`
to filter out weak matches:

| Value | Effect |
|---|---|
| `8` (recommended) | High-confidence matches only — fewer results, less noise |
| `5` | Moderate — captures more results but may include tangential mentions |
| omit | No threshold — returns everything, including weak associations |

Start at `8`. If the user reports too few results, lower to `5`.

**`ed_association_type` — entity association strength:**

When `connected_dataset_ids` is set, use `ed_association_type` to control how
strongly a watchlist entity must appear in each event:

| Value | Effect |
|---|---|
| `"event_associated"` | Keep only events where the entity is a **direct actor** (default when connected_dataset_ids is set) |
| `"mention"` | Keep all events where the entity is **merely referenced**, even in passing |

Use `"event_associated"` (or omit the parameter) for tight, high-signal results.
Use `"mention"` when the user wants broader coverage. All the simple mentions of the companies will be here, even if a company is not a main actor in the story
but simply mentioned somewhere in the text. Never use it, unless the user asks for it.

**`fetch_all_watchlist_news` — bypass topic filtering:**

When `True`, retrieves **all** news for connected watchlist entities without
applying topic filtering from `query`. Use this when the user wants a general
news feed for their watchlist rather than topic-specific results. This mode usually returns much more data than the topic related mode, but it also returns too much noise.
It is good when a user does not know exactly what they are looking for and want to explore everything that is available. But for Agentic and Data Pipelines, better not to use this parameter.
Requires `connected_dataset_ids` to be set. Default: `False`.

Also pass `fetch_all_watchlist_news=True` to `initialize_query` when you intend
to use it in `submit_query` — this ensures the previewed validators and
enrichments are generated to match the all-news intent.

**Query-writing rules when using connected datasets:**

- Write the `query` to describe the **topic or event type only** — for example,
  `"M&A activity"`, `"regulatory filings"`, `"executive changes"`. Do NOT write
  things like `"for my companies"`, `"for the selected list of companies"`, or
  `"news about my watchlist"` — entity filtering is applied automatically by the
  connected dataset. Mentioning companies in the query degrades retrieval quality.
- Entity-relevance validators (e.g. `company_is_primary_subject`) are generated
  **automatically** by the API when `connected_dataset_ids` is set. Do NOT add
  them manually to `validators` — they are redundant and may conflict with the
  auto-generated ones. Only pass validators that describe the event or topic
  (e.g. `is_acquisition_event`).
- The same rule applies in `context`: do not ask for entity-relevance validators
  there, and do not mention that a company list will be attached. Focus `context`
  on the event or topic specifics only.

**When to use watchlist mode:**

- "Track these 10 competitors" — named company list
- "Monitor news about our supplier list" — uploaded CSV of companies
- "What's been happening at these 50 clients" — known entity set

**When not to use it:** broad topic queries with no named entity list. Watchlist
mode narrows results to entities in the dataset — it will miss relevant events
involving companies not on the list.

**Dataset health:** `get_dataset_status` shows enrichment progress. A dataset
with low `health_score` (entities that failed enrichment) will produce fewer
results. Check it before large runs.

---

## Webhooks: delivery setup

Webhooks push job or monitor results to an external endpoint automatically.
Always test before attaching.

**Setup workflow:**

1. `create_webhook` — register the endpoint (name, url, type, auth). Pass
   `project_id` if you want the webhook associated with a project from the start.
2. `test_webhook` — verify it receives a payload correctly
3. `assign_webhook_resource` — attach the webhook to a job or monitor

**Delivery modes:**

| Mode | Behavior | Use when |
|---|---|---|
| `full` | One call with all results when job completes | Downstream system processes batches |
| `per_record` | One call per article as results arrive | Streaming pipelines, real-time triggers |

**Webhook types:** `generic` (raw JSON), `slack` (pre-formatted Slack message),
`teams` (pre-formatted Teams card), `custom` (user-defined formatter).

**Auth options:** `bearer` token, `api_key` (custom header + value), or `basic`
(username + password).

**Important:** A webhook attached to a monitor fires on every scheduled run
automatically — no extra steps needed after `assign_webhook_resource`.

---

## Projects: organizing work

Projects group related jobs, monitors, datasets, and webhooks together. Use them when:

- The user is running multiple related queries (e.g., "all my competitive intelligence work")
- Multiple team members share a workspace and need to filter by initiative
- The user wants an overview of all resources for a given topic

**Workflow:**

1. `create_project` — give it a name and description
2. Submit jobs / create monitors / build datasets / create webhooks as usual
3. `add_project_resources` — attach completed resources to the project
   (`resource_type` is one of: `job`, `monitor`, `dataset`, `monitor_group`, `webhook`)
4. `get_project_overview` — see counts by resource type and status

Projects are organizational only — they don't affect job processing or billing.
Deleting a project with `delete_resources: false` (the default) leaves all
resources intact. Even with `delete_resources: true`, webhooks are **never**
deleted — they are only detached from the project. The `deleted_resources` map
in the response includes a `webhook_unlinked` count for detached webhooks.

---

## Full automation workflow

The most common multi-step request — "alert me every week when X happens" —
requires wiring together jobs, monitors, and webhooks. Here is the complete
sequence:

1. **Submit a job** — `submit_query` with the user's query. Use a short window
   (last 7 days) to test that the query returns meaningful results.
2. **Review output with the user** — pull results, confirm the records are
   relevant. Refine query, validators, or enrichments if needed. Repeat until
   the user is satisfied.
3. **Create a webhook** — `create_webhook` with the delivery destination
   (Slack, Teams, or a generic URL). Pass `project_id` if the webhook should be
   associated with a project immediately. Run `test_webhook` to confirm it
   receives payloads before wiring it up.
4. **Create a monitor** — `create_monitor` using the completed job as
   `reference_job_id`, with the user's requested schedule and the webhook's
   `id` passed in `webhook_ids`.
5. **Confirm** — tell the user: what query will run, on what schedule, where
   results will be delivered.

This five-step sequence is the answer to prompts like:
- "Send me a Slack message every Monday with new fintech partnerships"
- "Alert me daily if any of our competitors raises funding"
- "Set up a weekly digest of EU regulatory actions to my email webhook"

---

## Monitor workflow

Monitors re-run a completed job's query on a schedule and push results to a
webhook. Follow the **explore → refine → automate** pattern:

1. **Explore** — submit a job, review results with the user
2. **Refine** — adjust query, validators, or enrichments until the output matches exactly what is needed
3. **Automate** — once the user is satisfied, create a monitor from that job using `create_monitor`

**Key parameters for `create_monitor`:**

| Parameter | Notes |
|---|---|
| `reference_job_id` | Must be a completed job — this is the template |
| `schedule` | Natural language with timezone: "every day at 9 AM EST", "every Monday at 8 AM UTC" |
| `backfill` | Default `true` — fills the gap between the reference job's end date and now. Only works if the reference job's end date is within the last 7 days. Set to `false` for forward-only monitors. |
| `webhook_ids` | Optional — attach one or more webhooks at creation time |
| `limit` | Per-run record cap (minimum 10); can be changed later via `update_monitor` |

For schedule syntax and natural-language examples, see
`references/MONITOR-SCHEDULING.md`.

Proactively suggest a monitor when the user has iterated on a query and is happy
with the output — especially for recurring needs like daily M&A deals, weekly
funding rounds, or ongoing topic tracking.

---

## Result presentation

**Always show the exact number of records returned — never fewer.**

- If the job returns 10 records → show all 10
- If the job returns 50 records → show all 50
- Never skip records or say "here are the highlights"

For each record, display by default:
- Full title (not truncated)
- Key enrichment fields if present
- At least one citation link (`citations[0].link` from the record)

The user set a `limit` for a reason. Silently reducing results breaks
expectations and wastes quota.

---

## No-results fallback

If a job returns zero valid records (`valid_records: 0`), escalate in steps:

1. **Check `candidate_records`** — if > 0, validators are too strict. Loosen them or resubmit with just the query (auto-validators). Tell the user.
2. **Check for over-constraining** — if the query has 5+ constraints, drop the most restrictive one first. Tell the user which was dropped.
3. **Expand the timeframe** — widen to 30 days if shorter. Tell the user.
4. **Expand the geography** — widen one level (city → region → country → global). Tell the user.
5. **Broaden the event type** — remove the most specific qualifier. Tell the user.
6. **Advise honestly** — if all steps produce nothing: "There may be limited coverage for this topic in the available sources."

Always explain what changed before resubmitting.

---

## Edge cases

| Scenario | Action |
|---|---|
| Job stuck in `fetching` for >5 min | Re-poll; if persistent, submit a new job |
| `valid_records: 0`, `candidate_records: 0` | Query produced no raw matches — broaden it |
| `valid_records: 0`, `candidate_records: N` | Validators filtered everything — loosen or remove validators |
| User asks for data beyond 30 days | Split into consecutive 30-day windows; run each as a separate job |
| Dataset status not `ready` | Wait for enrichment to complete before attaching to a job |
| Dataset `health_score` is low | Some entities failed enrichment — check `list_dataset_entities` for `status: failed` |
| Monitor returning 0 results after previously returning N | Run `get_monitor_status` to see state history; check if the reference job's validators have become too strict for the current news cycle — resubmit the reference job and create a new monitor if needed |
| Monitor webhook fails | Use `get_webhook_history` (resource mode: `resource_type` + `resource_id`) to diagnose; if the delivery was missed, use `trigger_webhook` to replay it on demand; then `update_monitor` or `update_webhook` to fix the underlying issue |
| Webhook delivery missed or needs replay | Use `trigger_webhook` with the webhook's ID and the target resource (`job`, `monitor`, or `monitor_group`); follow up with `get_webhook_history` to confirm the delivery outcome |
| Need to audit all deliveries through one webhook endpoint | Use `get_webhook_history` in webhook mode: pass `webhook_id` only (no `resource_type`/`resource_id`) |
| Manual test delivery not appearing in resource history | Test deliveries only appear in webhook-mode history (`webhook_id` param); they are recorded with `resource_type: "test"` |
| Tool call returns `isError=True` | Read the error message — it carries the upstream status code and detail (e.g. `API Error (401): Api key not found`). Do not retry blindly; fix the root cause (bad API key, invalid project_id, not-found ID) first |
| User wants to re-pull a past job | `list_user_jobs` to find the `job_id`, then `pull_results` |
| User wants to re-pull a past job as CSV | `list_user_jobs` to find the `job_id`, then `pull_job_csv` |
| User wants to list only lite-mode jobs | `list_user_jobs` with `mode="lite"` |
| User wants to share work with a teammate | Add resources to a project; teammates with access can filter by project |
| Connected dataset query returns too many irrelevant results | Verify query describes the topic only (not the entity list); check that entity-relevance validators are not being passed manually — the API generates them automatically |
| User deletes a project and asks why webhooks are still active | `delete_project` never deletes webhooks — it only detaches them; `deleted_resources.webhook_unlinked` shows the count of detached webhooks |
| User wants to scope a job to specific domains | Use `list_source_groups` to find the relevant group's `slug`, then pass it via `source_groups` on the direct `POST /catchAll/submit` API; `submit_query` (MCP tool) does not yet expose this parameter |
