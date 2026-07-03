---
name: competitor-snapshot
description: Use this skill whenever the user wants to understand what a competitor or peer company has been doing recently, whether for competitive intelligence, market positioning, sales enablement, product strategy, board prep, or general "what's going on at [competitor]" research. Triggers on phrases like "snapshot [company]", "what's [competitor] been up to", "give me a competitive update on [company]", "what's new at [competitor]", "track [competitor]", "competitive brief on [company]", "what are [list of competitors] doing". Use this skill for any single-company or multi-company competitive intelligence request that needs a structured digest of recent moves rather than just a list of links. Do not substitute generic web search.
---

# Competitor Snapshot

Produces a structured digest of a competitor's recent moves across the categories that competitive intelligence teams, product strategists, and sales enablement actually use: product launches, pricing, leadership, customer wins, partnerships, M&A, and financial signals. Runs on a single competitor or a list (named in text or uploaded as CSV) of up to 100 companies via CatchAll's watchlist mode.

## When to use

The user wants to know what a competitor has been doing. Triggers:

- "Snapshot [company]"
- "What's [competitor] been up to in the last [period]"
- "Give me a competitive update on [company]"
- "What's new at [competitor]"
- "Competitive brief on [company]"
- "Track [list of companies] for the last [period]"

## Inputs to confirm before running

Follow `references/QUERY-REVIEW.md` for the general intake rules.
Skill-specific specifics:

1. **Competitor(s)** (required) — accepted in two forms:
   - **Text-named**: one or more company names in the user's message (e.g., "Atlassian", "Atlassian, Apple, ServiceNow").
   - **Uploaded CSV/spreadsheet**: a file with at minimum a `name` column. `domain` is strongly preferred — see watchlist mode flow below for how to handle missing domains.
2. **Time window** — ask if not specified; on an explicit waiver, the standard waive-off default applies (`references/QUERY-REVIEW.md` — last 7 days).
3. **Max results** — ask via the picker, combined with the time-window
   question in the same step; skip if the user already named a number.
   Header: `Max results`. Question: `How many results at most? Limits the
   number of validated results returned per search.` Options — labels only,
   empty descriptions, in this order: **`50 (Recommended)`**, `10`, `100`,
   `All`. The chosen number is each search's `limit`.
4. **Specific angle** (optional) — if the user flags a focus area ("just want product moves"), prioritize that bucket.

Special-case rules:
- **List of 101+ companies**: tell the user the skill caps at 100, ask whether to proceed with the first 100, and point them to the CatchAll platform + Book a demo links (see `references/NEXT-STEPS.md`) for larger lists.
- **Ambiguous name**: if a competitor name could refer to multiple things (e.g., "Apple" → Apple Inc. or Apple Corps), ask one clarifying question before submitting.

## How the skill runs

**One execution path: always watchlist mode**, even when the user names
a single competitor. A single-competitor run builds a watchlist of 1
behind the scenes ({name: <competitor>, domain: <domain>}, no user
prompt for the upload). This means every event carries `ed_score`,
`relation`, and `is_developing` regardless of how many competitors the
user named.

The full watchlist mechanics (building the company list, domain
handling, the 100-company cap, building the dataset, submitting with
`connected_dataset_ids`, polling, and parsing `connected_entities`) are
in `references/COMPANY-WATCHLIST.md`. Follow that verbatim — do not
improvise, and do not write a helper script.

Watchlist mode runs entirely through the CatchAll MCP, so it works on
every platform with the MCP connected — claude.ai and ChatGPT included.
The only fallback is when the MCP lacks the watchlist tools (an older
CatchAll MCP): name every competitor directly in the bucket queries
(short list) or tell the user to update the MCP (long list). A fallback
is expected behavior, not an error. See `COMPANY-WATCHLIST.md`
§ Execution path.

Skill-specific details for competitor-snapshot:
- Dataset name slug: `competitor-snapshot`
- For single-competitor runs, build the watchlist silently in memory
  with one row — no upload-confirmation prompt to the user
- Run all 7 bucket queries below in their watchlist phrasing, connected
  to the dataset, with each bucket's own `enrichments` plus the
  cross-cutting `is_developing` enrichment
- Attribute each event to its highest-`ed_score` company in
  `connected_entities`; that name populates the `competitor` field
- Surface in chat only events whose attributed company scores
  `ed_score >= 8` (`COMPANY-WATCHLIST.md` Step 4) — those count toward
  "events found"; everything lower-scored goes to the JSON/CSV downloads
  only

The chat **output template** varies by watchlist size:
- 1 company → single-competitor template (no Company column, no at-a-glance)
- 2+ companies → multi-competitor template (Company column, at-a-glance table)

### Load more

Each bucket's `limit` is the number chosen in the `Max results` picker.
If any bucket hits that cap (`valid_records == limit`), add a short note
under that bucket's table in chat: `Showing [limit] of [N estimated].
Ask to load more.` If the user asks to load more, call `continue_job`
with a new higher limit, repoll to terminal, re-pull all pages, and
regenerate the xlsx, JSON, and CSV files atomically.

## Bucket queries

Run CatchAll for each of the 7 buckets below. In single-competitor
path, the query names the competitor. In watchlist-mode, the query
omits the company name (the `connected_dataset_ids` parameter scopes
the search to the watchlist).

> **Before submitting any jobs**, read `references/QUERY-REVIEW.md`.
> It defines when to confirm scope and parameters with the user vs.
> proceed with defaults. Critical for multi-competitor runs and any
> query where the time window isn't specified.

> **For the watchlist mechanics** (building the company list, batch-
> creating entities, the dataset, connected submits, attribution), read
> `references/COMPANY-WATCHLIST.md` — every run uses it (single-competitor
> runs build a watchlist of 1).

> **Then read `references/JOB-LIFECYCLE.md`** (per-search contract:
> pre-flight, host-aware polling, completion detection, failure handling)
> **and `references/CONCURRENCY.md`** (the multi-search layer: waves, the
> live progress table, checkpoints, no time cap, re-poll on follow-up).
> Follow both verbatim — do not improvise. The progress table uses
> per-category rows (one row per bucket) and the same row structure
> persists across every checkpoint, with status emojis and live counts
> updating in place.

> **Before writing output**, read `references/OUTPUT-REPORT.md`
> (xlsx + JSON + CSV full-dataset contract: file naming, schema, columns, the
> `Full dataset:` block, vocabulary, dates) and `references/NEXT-STEPS.md`
> (the **More with CatchAll** footer that closes every chat output).

Submit queries in concurrency-sized waves (see `references/CONCURRENCY.md`
— read the concurrency limit first, open with the generous time estimate
and the kickoff table). **Each bucket is an independent CatchAll query.**
Some events plausibly fit two buckets (e.g., an earnings release that
mentions a layoff). Do not move events between buckets after pull —
render each bucket's results as CatchAll returned them.

Note: "wave" and "bucket" are implementation vocabulary only — **they
never appear in user-facing text.** A unit of work is a **search**; table
rows say `Searching <category>` (see `references/CONCURRENCY.md`).

### Cross-cutting enrichment (every bucket)

Every bucket below additionally includes one shared enrichment that
powers the "Events worth watching" section. Add it to every bucket's
`enrichments` array alongside the bucket-specific fields listed in
each subsection:

- `is_developing` (option, values: `true | false`): "True ONLY if the event meets one of these specific criteria: (1) RUMORED or REPORTEDLY happening — not officially confirmed by the company; (2) IN ACTIVE NEGOTIATION or discussion with outcome not yet finalized (e.g., 'in talks to acquire'); (3) officially announced with a SPECIFIC FUTURE effective date that has not yet arrived (e.g., 'CEO joins August 1', 'price increase takes effect Q3 2027', 'product ships Q4'); or (4) PRE-GA / BETA / PREVIEW product releases. False for everything else, including: completed launches and announcements where the product/change is already available, earnings reports and quarterly results, headlines using 'unveils' / 'announces' / 'launches' about things that ARE available now, and ongoing industry trends. When in doubt, default to false."

The skill renders a cross-bucket "Events worth watching" section out of
events flagged `true` — see § Events worth watching — selection rule.

### 1. Product and feature launches

- **Single-competitor query**: `Product launches, new feature announcements, and major releases by [Competitor] in the last [window]`
- **Watchlist query**: `Product launches, new feature announcements, and major releases by companies in this watchlist in the last [window]`

Enrichments:
- `product_name` (text): "The product or feature being launched or updated"
- `announcement_type` (option, values: `launch | new_feature | beta | ga`): "Type of product announcement"
- `release_stage` (text): "Release maturity, e.g. GA, Beta, Preview, Public Preview"

### 2. Pricing and packaging changes

- **Single-competitor query**: `Pricing changes, new plans, packaging updates, and commercial model shifts at [Competitor] in the last [window]`
- **Watchlist query**: `Pricing changes, new plans, packaging updates, and commercial model shifts at companies in this watchlist in the last [window]`

Enrichments:
- `change_type` (option, values: `price_increase | new_tier | freemium | restructure | discount`): "Nature of the pricing or packaging change"
- `affected_tier` (text): "Plan or tier affected, e.g. Standard, Premium, Enterprise"

### 3. Leadership and key hires

- **Single-competitor query**: `Executive appointments, senior hires, and leadership departures at [Competitor] in the last [window]`
- **Watchlist query**: `Executive appointments, senior hires, and leadership departures at companies in this watchlist in the last [window]`

Enrichments:
- `executive_name` (text): "Name of the executive joining, leaving, or moving"
- `role` (text): "Role or title, e.g. CFO, Head of AI, SVP Engineering"
- `move_type` (option, values: `hire | departure | promotion | board_change`): "Type of leadership move"

### 4. Customer wins and case studies

- **Single-competitor query**: `Named-customer announcements, customer case studies, and named-customer deployments OF [Competitor] products in the last [window]`
- **Watchlist query**: `Named-customer announcements, customer case studies, and named-customer deployments OF products from companies in this watchlist in the last [window]`

Enrichments:
- `customer_name` (text): "Name of the customer organization"
- `win_type` (option, values: `new_customer | expansion | case_study | renewal`): "Type of customer win"
- `industry` (text): "Customer industry or vertical, e.g. financial services, manufacturing"

### 5. Partnerships and integrations

- **Single-competitor query**: `Strategic partnerships, integrations, and alliance announcements involving [Competitor] in the last [window]`
- **Watchlist query**: `Strategic partnerships, integrations, and alliance announcements involving companies in this watchlist in the last [window]`

Enrichments:
- `partner_company` (company): "The partner organization — the other company in the partnership or integration, different from the company the snapshot is about. Null if no external partner is named."
- `integration_type` (option, values: `technology | channel | co_marketing | reseller | embedded`): "Nature of the partnership"
- `products_involved` (text): "Products involved in the partnership"

### 6. M&A and strategic moves

- **Single-competitor query**: `Acquisitions, divestments, fundraising, and strategic investments involving [Competitor] in the last [window]`
- **Watchlist query**: `Acquisitions, divestments, fundraising, and strategic investments involving companies in this watchlist in the last [window]`

Enrichments:
- `target_company` (company): "The company on the receiving side of the deal — the one being acquired or invested in, not the acquirer/investor. Null if not applicable."
- `deal_value` (number): "Announced deal value in USD; null if not disclosed"
- `deal_type` (option, values: `acquisition | divestment | investment | funding_round | acqui_hire`): "Type of deal"

### 7. Financial and earnings signals

- **Single-competitor query**: `Financial results, earnings, revenue milestones, and guidance from [Competitor] in the last [window]`
- **Watchlist query**: `Financial results, earnings, revenue milestones, and guidance from companies in this watchlist in the last [window]`

Enrichments:
- `metric_type` (option, values: `revenue | eps | guidance | margins | layoffs | buyback`): "Type of financial signal"
- `value` (text): "Reported value with units, e.g. '$1.8B revenue', 'EPS $1.75', '~1,600 roles'"
- `report_period` (text): "Reporting period, e.g. Q3 FY2026, FY2025"

## Output

Every run produces four deliverables: a markdown chat response, an xlsx
workbook, a JSON file, and a CSV file. See `references/OUTPUT-REPORT.md`
for the file naming, sheet/column structure, schema, vocabulary, date
formatting, table conventions, and zero-event pattern.

The chat response is a compressed summary. Full enumeration lives in
the full dataset (the xlsx, JSON, and CSV files). Lead with the dataset;
the strategic reading is the reader's job, not the skill's.

### Per-bucket table columns

Use "events found" universally in section headers. The table per bucket
has different columns based on what data the bucket naturally produces.

| Bucket | Table columns (after Event, Date; before Sources) |
|---|---|
| Product and feature launches | Product, Stage |
| Pricing and packaging changes | Change type, Affected tier |
| Leadership and key hires | Role, Move type |
| Customer wins and case studies | Customer, Win type |
| Partnerships and integrations | Partner, Integration type |
| M&A and strategic moves | Target, Deal value |
| Financial and earnings signals | Metric, Value |

All tables share **Event** as first column and **Sources** as last
column. **In watchlist-mode runs, add a `Company` column immediately
after `Event`** (sourced from each event's `connected_entities`). The
middle columns are bucket-specific. If CatchAll's enrichments don't
include a column listed here, render the cell as `—`. If CatchAll
returns *additional* useful enrichments, append them as extra columns
before Sources.

Do not add a column for `ed_score` or `relation` — the chat shows only
the `ed_score >= 8` events; everything lower-scored lives silently in
the full dataset. The reader never sees the scoring at all.

**Event title length**: truncate event titles to ~100 characters
(append `…` if truncated). **Date cells**: write the
month and day joined by a non-breaking space (U+00A0) — e.g. `May·20`
with a non-breaking space — so a short date never wraps to two lines in
a narrow column.

### Chat response — single competitor

```
# [Competitor] — Competitive Snapshot

Full dataset:
  JSON: [absolute path to .json]
  CSV:  [absolute path to .csv]

## CatchAll findings

| Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|
| [May 13–20, 2026] | [May 20, 2026] | Base | **[M]** | **[N]** |

---

## Product launches — [m] web pages scanned · [n] events found

| Event | Date | Product | Stage | Sources |
|---|---|---|---|---|
| [event title, ≤100 chars] | [May 16] | [product] | [GA/Beta/Preview] | [domain] + [k] others |
| ... up to 10 rows in chat ... |

([n-10] more in the full dataset)

---

## Pricing and packaging — [m] web pages scanned · [n] events found

| Event | Date | Change type | Affected tier | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## Leadership and hires — [m] web pages scanned · [n] events found

| Event | Date | Role | Move type | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## Customer wins — [m] web pages scanned · [n] events found

| Event | Date | Customer | Win type | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## Partnerships and integrations — [m] web pages scanned · [n] events found

| Event | Date | Partner | Integration type | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## M&A and capital — [m] web pages scanned · [n] events found

| Event | Date | Target | Deal value | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## Financial signals — [m] web pages scanned · [n] events found

| Event | Date | Metric | Value | Sources |
|---|---|---|---|---|
| [≤10 rows or empty-table pattern if n=0] |

---

## [n] events worth watching

_Early signals on rumored, in-talks, planned, or upcoming stories._

| Event | Date | Category | Sources |
|---|---|---|---|
| [event title, ≤100 chars] | [May·18] | [M&A] | [bloomberg.com] + [k] others |
| ... up to 10 rows ... |

(K more — filter on `is_developing` in the full dataset)

(Render this section only if ≥1 event qualifies — see § Events worth watching — selection rule. Omit the trailing "K more" line when K = 0.)

---

## Analysis
- **Top story**: [Name the most-covered event. First sentence: name the story + how broad the coverage was (number of publishers, languages, dates). Second sentence: what aspects of the story were covered, e.g. revenue print, AI strategy, workforce action.]

- [Cross-category story bullet — see formats below. Omit entirely if no story genuinely spans 2+ categories.]

[Paste the **More with CatchAll** footer verbatim from `references/NEXT-STEPS.md` — the `---` rule, the `## More with CatchAll` heading, and the link line (watchlist link on watchlist runs only). Never type the URLs from memory.]
```

The chat output ends with the **More with CatchAll** footer — see
`references/NEXT-STEPS.md` for the exact links and URLs. The
company-watchlist link is included for watchlist-mode runs and omitted
for single-competitor runs.

The analysis section never has more than two bullets. Both must add
something the reader couldn't easily glean from the per-bucket tables.
Do not pad with derivative observations.

### Cross-category story formats

When exactly one event genuinely spans 2+ categories, lead the bullet
with the event name and explain how it lands in each:

```
- **Cross-category story**: Atlassian's Q3 FY26 earnings appear under both **Customer wins** (where the AI/cloud growth narrative and the ~1,600-role workforce action landed) and **Financial signals** (where the revenue print landed) — same story, two angles.
```

When 2+ events span categories, use a labeled bullet with sub-bullets:

```
- **Stories that spanned multiple categories**:
  - **Q3 FY26 earnings** — appears in Customer wins (AI/cloud growth + 1,600-role workforce action) and Financial signals (the revenue print)
  - **Flex AI licensing rollout** — appears in Product launches (the new licensing feature) and Pricing & packaging (the commercial model shift)
```

The parenthetical explains *why* the story landed in each category, so
the reader understands the framing and doesn't think it's a duplicate.

### Analysis section language rules

- Use **display names** for categories (Customer wins, Financial
  signals), never the JSON keys (`customer_wins`, `financial_signals`).
- Avoid CatchAll internal vocabulary: "cluster," "citation," "signal,"
  "bucket," "candidate." Use plain words: story, event, coverage,
  publisher, article, category.
- Do not mention implementation details like "each bucket is an
  independent CatchAll call." The reader doesn't need to know that.
- Each bullet is one sentence (or one short clause + parenthetical).
  No paragraphs.
- Use "window" not "week" so phrasing generalizes across 7-day, 30-day,
  or longer queries.

### Empty-table pattern for zero-event sections

When a bucket has 0 events, do NOT omit the table — render the header
row (which shows the data shape) plus a single italicized row:

```
| Event | Date | Target | Deal value | Sources |
|---|---|---|---|---|
| _No events found in this window._ |  |  |  |  |
```

Use exactly `_No events found in this window._` as the first cell;
leave all other cells blank (no em-dashes — em-dashes imply "no data
for this field" rather than "no row exists"). No commentary about
what the candidate noise was. The `noise_description` for that bucket
stays in the JSON for pipelines. This pattern is required by
`OUTPUT-REPORT.md`.

### Output integrity rules

These prevent common rendering bugs:

- **Render all 7 bucket sections, in the exact order above, every
  time.** A bucket with 0 events still gets its dashboard line and
  empty-table pattern. Do not skip.
- **Each section's table belongs to that section.** Do not borrow
  rows from another bucket. If a section is empty, use the empty-table
  pattern — do not fill its rows with the next bucket's events.
- **Render each section's table exactly once.** No duplicates, no
  repeated header rows.
- **Insert a horizontal rule (`---`) on its own line between every
  section** (after the prior section's last line, before the next
  section's `##` header). A blank line collapses to minimal vertical
  space in most renderers; `---` draws a thin line with padding above
  and below, giving the eye a clear break between sections. The existing
  `---` immediately before the **More with CatchAll** footer is part of
  this same pattern.
- **Use the short date form `May 16` (no year) inside table cells.**
  Full `May 16, 2026` wraps to two lines in narrow columns; the year
  is already carried by the window header.

### No agent-written caveats — hard rule

**Do not add caveats, asterisks, footnotes, warnings, ⚠ symbols, or
any other commentary about data quality or possible misattribution
to the output.** The skill renders raw CatchAll output as-is. If a
validator misattributes an event (e.g., catches the wrong company),
that fact stays in the output and the user evaluates it.

This applies to:
- Event titles: no asterisks on titles
- Row markers: no `⚠` or `*` on rows
- Bottom-of-output sections: no "Caveats", "Notes", "Verify before
  using" sections
- Parenthetical aside in tables: no "(verify before citing)" hints
- The JSON: no `meta.caveats[]` array of agent observations
- **No explaining the mechanics.** Never write a "One note on the
  data:" line, never tell the reader how watchlist matching works or
  that results were scored or filtered, and never put the words
  "subject", "peripheral", "ed_score", or "mention-based" in the
  output. The reader sees the tables and `([n] more in the full
  dataset)` — nothing about how the result was produced.

This is non-negotiable. Do not flag attribution corrections (e.g. "Dia
is The Browser Company's product"), and do not append data-quality notes
(e.g. "One note on the data: …"). Show the data. Trust the user to
evaluate it.

The only thing the skill writes about run quality is `meta.run_flags[]`
in the JSON, and only for operational issues (job failed, results pulled
before completion). These stay in JSON only — never in chat.

### Chat response — multi-competitor (watchlist mode)

Lead with the dashboard panel + at-a-glance table, then 7 bucket
sections (same as single-competitor) — but each event row now has a
`Company` column from `connected_entities`. The per-bucket tables show
events across the entire watchlist, with attribution per row.

```
# Competitive Landscape Snapshot

Full dataset:
  JSON: [absolute path to .json]
  CSV:  [absolute path to .csv]

## CatchAll findings

| Watchlist | Companies | Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|---|---|
| [dataset name] | [N companies] | [May 13–20, 2026] | [May 20, 2026] | Base | **[M]** | **[N]** |

---

## At a glance

| Company | Events found |
|---|---|
| Alpha | 14 |
| Beta | 3 |
| Gamma | 21 |

---

## Product launches — [m] web pages scanned · [n] events found

| Event | Company | Date | Product | Stage | Sources |
|---|---|---|---|---|---|
| [event title, ≤100 chars] | [Alpha] | [May 16] | [product] | [GA] | [domain] + [k] others |
| [≤10 rows in chat; load-more note appears under the table if cap was hit] |

([n-10] more in the full dataset)

---

[All other buckets follow the same pattern, with the bucket-specific
middle columns from the table above, plus the Company column after
Event. Each bucket is separated from the next by a `---` horizontal rule.]

---

## [n] events worth watching

_Early signals on rumored, in-talks, planned, or upcoming stories._

| Event | Company | Date | Category | Sources |
|---|---|---|---|---|
| [event title, ≤100 chars] | [Alpha] | [May·18] | [M&A] | [bloomberg.com] + [k] others |
| ... up to 10 rows ... |

(K more — filter on `is_developing` in the full dataset)

(Render this section only if ≥1 event qualifies — see § Events worth watching — selection rule. Omit the trailing "K more" line when K = 0.)

---

## Analysis
[Same two-bullet Analysis section as the single-competitor template.]

[Paste the **More with CatchAll** footer verbatim from `references/NEXT-STEPS.md` — the `---` rule, the `## More with CatchAll` heading, and the link line (watchlist link on watchlist runs only). Never type the URLs from memory.]
```

**Chat tables and every "events found" count show only the events whose
attributed company scores `ed_score >= 8`** — the ones genuinely about
a monitored company. Events where a monitored company is only a former
employer, comparison, or background mention score lower and drop
silently into the JSON/CSV full dataset, never appearing in chat. The
reader is not shown the scoring at all; the `([n-10] more in the full
dataset)` line is all they see. See `COMPANY-WATCHLIST.md` Step 4.

### Load-more note (when a bucket hit the cap)

When any bucket's `valid_records` equals the chosen `limit`, append a
single italicized line directly below that bucket's table:

```
_Showing [limit] of [estimated total] events. Ask to load more if you want the full set._
```

The estimated total can be inferred from `candidates_scanned` or omitted
if uncertain (just say `[limit] of more`). When the user asks to load
more, call `continue_job` with a higher `new_limit`, repoll to terminal,
re-pull all pages, then regenerate the xlsx, JSON, and CSV files
atomically and re-render the chat output. Do not append; rewrite.

### Events worth watching — selection rule

The "Events worth watching" section surfaces forward-looking events the
user can act on before they're complete (rumored deals, planned launches,
in-talks partnerships). Selection is mechanical — same data in, same
events out, no agent judgment:

1. Start from all events where `is_developing == true`
2. Filter `ed_score >= 8` (same centrality bar as the main buckets — the section is about your watchlist companies, not adjacent ones)
3. Dedup by title across buckets — if the same event appears in two buckets, keep the row from the bucket where it scored highest
4. Sort by citation count desc (same sort as the main bucket tables — see `OUTPUT-REPORT.md` § Tables for event lists)
5. Take top 10 (matches the cap used in every bucket table — same number everywhere keeps the reader's mental model consistent)

In the xlsx, emit `meta.spotlights[].columns`: `company, category, title, date, citation_count, citations, summary` — `category` (the originating bucket's display name) is the one extra column, supplied on each membership row. On a single-company snapshot the `company` cell is just that company.

If 0 events remain after filtering, skip the section entirely. There is
no empty-table pattern here — unlike the main buckets, the absence of
mid-stream events is not itself a finding worth showing.

If more than 10 events qualify, append the trailing line
`(K more — filter on \`is_developing\` in the full dataset)` immediately
below the table (K = qualifying count − 10). Omit the line when K = 0.

Companies that appear here may also appear in the main bucket tables —
that's expected (this is a cross-cutting view, not a separate query).
The `Category` column lets the reader cross-reference to the main section.

**Not counted toward "Total events found"** on the dashboard. That
headline stays a count of completed events. This section is forward-
looking and by definition less certain, so it sits separately.

**Available on every run** — single-competitor included. Since single-
competitor is built as a watchlist-of-1, every event carries
`ed_score`, so the same selection rule applies uniformly. The
single-competitor template renders the section without the `Company`
column (the company is the run's subject and would be the same on every
row).

### What this output deliberately does not include

- **No "So what" / strategic interpretation.** The skill enumerates;
  the reader interprets.
- **No narrative headline collapsing multiple events into a story.**
  Each event is one row in the table. The narrative emerges from the
  numbers, not from the prose.
- **No editorial framing in section bodies.** Event titles and short
  factual summaries only. Save the analysis for the reader.

If the user explicitly asks for a strategic interpretation after seeing
the snapshot, that's a follow-up — not part of the default deliverable.

## Length discipline

- Run-level subhead: 1 line, mostly numbers
- Per-bucket section: ≤ 10 events in chat, rest in the full dataset
- Zero-event sections: render the empty-table pattern (do not omit)
- Analysis: at most 2 bullets, factual only — no interpretation
- Single-competitor chat output fits on roughly one screen, plus the optional "Events worth watching" section (≤10 rows, only renders if any event qualifies)
- Multi-competitor: dashboard panel + at-a-glance table + 7 bucket sections (each with a Company column) + optional "Events worth watching" section (≤10 rows, only renders if any event qualifies). Bucket sections cap at 10 events in chat regardless of how many companies contributed.

## Handling edge cases

| Scenario | Action |
|---|---|
| Quiet quarter (most buckets zero) | Render each zero-event bucket with its candidate count + noise description. The "low activity" framing comes through from the per-bucket numbers naturally — no need to say "quiet quarter" anywhere. |
| Competitor is a household name with overwhelming volume | Filter to material moves. A Fortune 100 has signal noise; the job is finding the few moves that matter. |
| List includes both direct and indirect competitors | Note this in the at-a-glance — direct vs adjacent. Don't try to force equivalence. |
| Competitor is private with thin coverage | Note in headline that coverage is sparse. Suggest the user pair with a separate run on the founder/CEO if a key person is named in the available coverage. |
| User asks for "what should we do about it" | This skill produces the digest. Strategy recommendations are downstream. Offer to hand off to a strategy discussion separately. |
| Competitor was just acquired or merged | Lead with that in headline. Most other signals get reinterpreted through the deal. |

## What this skill does NOT do

- Does not produce a feature-by-feature comparison (that's a different exercise)
- Does not score competitive threat or assign ratings
- Does not pull from internal CRM data (only public signals via CatchAll)
- Does not set up monitoring (one-shot snapshot only — if the user wants ongoing tracking, suggest setting up a monitor on the same query bundle)
- Does not draft sales objection-handling content based on findings (separate workflow)

If the user wants to set up ongoing competitor tracking after seeing the snapshot, the natural next step is converting these queries into a recurring monitor via the standard CatchAll monitor workflow.
