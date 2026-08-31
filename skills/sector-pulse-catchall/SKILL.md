---
name: sector-pulse-catchall
description: Use this skill when the user wants a pulse read on an entire sector or industry — what moved across regulation, technology, demand, and capacity in one brief — scoped by a sector and geography rather than a company list. Triggers on "pulse report on [sector]", "sector pulse for [industry]", "industry pulse", "what's happening in the [sector] sector", "what's moving in [industry] in [region]", "give me a read on the [sector] market". Works for any sector and geography, timeframe up to 30 days. Do NOT use for tracking a named company list (competitor-snapshot-catchall or portfolio-monitoring-catchall), for funding-only or M&A-only queries (fundraising-catchall or mergers-and-acquisitions-catchall), or for a sector's combined funding and M&A picture (vc-pack-catchall).
---

# Sector Pulse

Produces a structured pulse brief on a whole sector — the events that
moved it in the window — in four categories sector watchers act on:
**regulation & policy, technology & product, demand & commercial, and
capacity & footprint**. Runs on a sector plus an optional geography (no
company list) and closes with **Events worth watching** — the developing
situations, ordered by when they land.

## When to use

The user wants to know what changed across a market, not at named
companies. Triggers:

- "Pulse report on the European energy sector for the last 30 days"
- "Sector pulse for cybersecurity"
- "What's happening in the semiconductor sector"
- "What's moving in fintech in Latin America"
- "Give me a read on the defense tech market"

For a named company list, use competitor-snapshot-catchall or
portfolio-monitoring-catchall. For funding rounds only, use
fundraising-catchall; for M&A only, use mergers-and-acquisitions-catchall;
for a sector's combined funding-and-M&A picture, use vc-pack-catchall.

## Inputs to confirm before running

Follow `references/QUERY-REVIEW.md` for the general intake rules.
Skill-specific specifics:

1. **Sector** (required) — an industry, vertical, or product category
   ("energy", "cybersecurity", "humanoid robotics"). If the name could
   refer to multiple markets, ask one clarifying question before
   submitting.
2. **Geography** (optional) — city, region, country, or "global."
   Defaults to global if unspecified.
3. **Time window** — ask if not specified. Sector activity reads on a
   monthly cadence, so the **waive-off default is the last 30 days**
   (not 7).
4. **Max results** — ask via the picker, combined with the time-window
   question in the same step; skip if the user already named a number.
   Header: `Max results`. Question: `How many results at most? Limits
   the number of validated results returned per search.` Options —
   labels only, empty descriptions, in this order: **`50
   (Recommended)`**, `10`, `100`, `All`. The chosen number is each
   search's `limit`.
5. **Specific angle** (optional) — if the user flags a focus ("just the
   regulatory side"), still run all four searches; section order does
   not change.

## How the skill runs

Four independent CatchAll searches, one per category below. There is no
company list — the sector and geography live in the query text — and
every search carries the same cross-cutting enrichments plus its own
category fields.

> **Before submitting any searches**, read `references/QUERY-REVIEW.md`
> (when to confirm scope vs. proceed), then
> `references/JOB-LIFECYCLE.md` (per-search contract) and
> `references/CONCURRENCY.md` (the multi-search layer: waves, the live
> progress table, checkpoints, no time cap, re-poll on follow-up).
> Follow all three verbatim. The progress table uses one row per
> search, labelled with the category display names; the same rows
> persist across every checkpoint with status emojis and live counts
> updating in place.

> **Before writing output**, read `references/OUTPUT-REPORT.md` (xlsx +
> JSON + CSV contract: file naming, schema, columns, the `Full
> dataset:` block, the spotlight slot, vocabulary, dates) and
> `references/NEXT-STEPS.md` (the **More with CatchAll** footer).

Submit in concurrency-sized waves (`references/CONCURRENCY.md`). **Each
category is an independent CatchAll search.** Some events plausibly fit
two categories (a subsidised factory build is policy and capacity);
render each category's results as CatchAll returned them — do not move
events between categories after pull. "Bucket" and "wave" are
implementation words; they never appear in user-facing text. A unit of
work is a **search**.

### Load more

Each search's `limit` is the number chosen in the `Max results` picker.
If any search hits that cap (`valid_records == limit`), add a short
note under that category's table: `Showing [limit] of [N estimated].
Ask to load more.` On request, call `continue_job` with a higher limit,
repoll to terminal, re-pull all pages, and regenerate the xlsx, JSON,
and CSV atomically.

## Cross-cutting enrichments (every search)

Add these four to every search's `enrichments` array alongside the
category-specific fields:

- `company` (company): "The company at the centre of the event — the
  one acting or acted on. Null if no single company is central, e.g. a
  sector-wide rule or an industry-wide shortage."
- `sub_sector` (text): "The specific sub-sector within [sector] this
  event belongs to (e.g. 'grid storage', 'offshore wind' for energy;
  'identity', 'fraud' for cybersecurity) — never the umbrella sector
  name itself. One short lowercase phrase, and use the SAME label for
  the same concept on every event: pick the shortest form that is still
  specific ('battery storage'), never a second wording for it later
  ('energy storage', 'battery energy storage system'). No comma-joined
  lists."
- `summary` (text): "One or two sentence factual summary of the event,
  drawn from the sources."
- `is_developing` (option, values: `true | false`): "True ONLY if the
  OUTCOME IS NOT YET DECIDED and could still change: (1) RUMORED or
  REPORTEDLY happening — not officially confirmed; (2) IN ACTIVE
  NEGOTIATION or under review with the outcome not settled (e.g. 'in
  talks', a bid under consideration, a permit application pending); or
  (3) a FILED-BUT-NOT-DECIDED step (e.g. a rule proposed or in
  consultation and not yet adopted, a WARN notice filed ahead of
  layoffs). **False when the decision is already made**, even if the
  effect lands later — a signed contract, an approved plant, an adopted
  rule with a future effective date, and an announced launch are all
  DONE, not developing. Also false for completed events, earnings
  results, and ongoing trends. When in doubt, default to false — this
  flag should apply to a minority of events."

## The four searches

Run CatchAll for each category. When the geography is global, drop the
"in [geography]" clause.

### 1. Regulation & policy

- **Query**: `New regulations, policy proposals, regulatory rulings and
  enforcement actions, subsidies, tariffs, and standards affecting the
  [sector] sector in [geography] in the last [window]`

Enrichments:
- `policy_stage` (option, values: `proposed | consultation | enacted |
  in_force | enforcement_action | struck_down`): "Where the measure
  stands. proposed = drafted or announced, not yet adopted;
  consultation = open comment or review period; enacted = adopted or
  passed with its effective date ahead; in_force = now applies;
  enforcement_action = a regulator or court acted against a party under
  an existing rule (fine, order, injunction); struck_down = blocked,
  overturned, withdrawn, or repealed."
- `authority` (text): "The regulator, legislature, court, or standards
  body involved, e.g. 'European Commission', 'SEC',
  'Bundesnetzagentur'; null if none named."

### 2. Technology & product

- **Query**: `Product launches, major releases, technology
  breakthroughs, patent grants, and new technical standards from
  companies and organizations in the [sector] sector in [geography] in
  the last [window]`

Enrichments:
- `event_type` (option, values: `launch | update | breakthrough |
  patent | standard`): "launch = a new product or service; update = a
  major release or upgrade of an existing one; breakthrough = a
  research or technical milestone; patent = a patent granted or filed;
  standard = a technical standard adopted or published."
- `availability` (option, values: `available | beta | pilot |
  announced`): "How real it is. available = commercially available now;
  beta = limited or test release; pilot = pilot program or
  demonstration deployment; announced = announced but not yet
  available. Null for patents, standards, and research results."

### 3. Demand & commercial

- **Query**: `Contract awards, customer wins, adoption milestones,
  pricing changes, and commercial partnerships in the [sector] sector
  in [geography] in the last [window]`

Enrichments:
- `event_type` (option, values: `contract_win | adoption | pricing |
  partnership`): "contract_win = a contract award or named customer
  win; adoption = an adoption or usage milestone; pricing = a price
  change or a new pricing model; partnership = a commercial partnership
  or distribution deal."
- `counterparty` (company): "The other party to the event — the buyer,
  customer, or partner. A different company than the one the event is
  about; null if none is named."
- `amount` (text): "Reported value of the contract or deal with its
  currency as stated, e.g. '$2.4B over 5 years', '€450M'; null if
  undisclosed."

### 4. Capacity & footprint

- **Query**: `Capital spending programs, new or expanded plants,
  factories and data centers, mass hiring, site closures, layoffs, and
  supply disruptions in the [sector] sector in [geography] in the last
  [window]`

Enrichments:
- `event_type` (option, values: `capex | facility | hiring | closure |
  layoffs | disruption`): "capex = a capital-spending program or
  investment commitment; facility = a new or expanded plant, factory,
  data center, or site; hiring = a mass-hiring push; closure = a site
  or line shut down; layoffs = a workforce reduction; disruption = a
  shortage, outage, strike, or other supply interruption."
- `scale` (text): "Magnitude where stated, e.g. '30 GW', '2 fabs',
  '4,000 jobs', '$10B program'; null otherwise."
- `location` (text): "Site or region of the event where stated, e.g.
  'Ohio', 'Dresden', 'Gujarat'; null otherwise."

## Output

Every run produces four deliverables: a markdown chat response, an xlsx
workbook, a JSON file, and a CSV file. See
`references/OUTPUT-REPORT.md` for file naming, sheet/column structure,
schema, vocabulary, date formatting, the spotlight slot, and the
zero-event pattern. Slug: `<sector-slug>-sector-pulse`, with the
geography in the slug when one was named (e.g.
`european-energy-sector-pulse`, `cybersecurity-sector-pulse`).

Manifest specifics for this skill:

- `meta.entity`: the sector, with the geography in parentheses when
  named — e.g. `Energy (Europe)`.
- `meta.aggregate_counts`: `["sub_sector"]` — the digest then carries
  the sub-sector counts for the At a glance table.
- `spotlights_meta`:

```json
[
  { "key": "events_worth_watching", "name": "Events worth watching",
    "subtitle": "Developing situations — rumored, in talks, or filed and not yet decided.",
    "columns": ["company", "category", "sub_sector", "title", "date", "citation_count", "citations", "summary"] }
]
```

Each membership row carries `record_id`, `category` (the originating
category's display name), and `sub_sector`. When the spotlight doesn't
render (no event qualifies), leave its membership list empty.

The chat response is a compressed brief; full enumeration lives in the
xlsx, JSON, and CSV. Lead with the dataset.

### Per-category table columns

Six columns per table, **Event** first and **Sources** last throughout.
`sub_sector` gets a column in every table so the At a glance counts are
navigable — a reader who sees `offshore wind 6` can find those six
events:

| Category | Columns |
|---|---|
| Regulation & policy | Event · Sub-sector · Date · Stage · Authority · Sources |
| Technology & product | Event · Company · Sub-sector · Date · Type · Sources |
| Demand & commercial | Event · Company · Sub-sector · Date · Type · Sources |
| Capacity & footprint | Event · Company · Sub-sector · Date · Type · Sources |

Regulation & policy carries no Company column — a sector-wide rule has
no single company, so the cell would be empty on most rows. Availability,
Counterparty, Amount, Scale, and Location are in the xlsx, JSON, and CSV
rather than in chat.

If an enrichment is missing, render the cell as `—`. Render option
values in friendly form in chat (`in_force` → `In force`,
`contract_win` → `Contract win`); JSON/CSV keep the raw values.
**Event titles**: truncate to ~100 characters (append `…`). **Date
cells**: short form `May 16` with a non-breaking space (U+00A0).

### Chat response

Lead with the dashboard panel + At a glance, then the four category
sections, then Events worth watching, then Analysis, then the footer.

```
# [Sector] — Sector Pulse

Full dataset:
  xlsx: [absolute path to .xlsx]
  JSON: [absolute path to .json]
  CSV:  [absolute path to .csv]

## CatchAll findings

| Sector | Geography | Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|---|---|
| [Energy] | [Europe] | [Jul 9 – Aug 7, 2026] | [Aug 7, 2026] | Base | **[M]** | **[N]** |

---

## At a glance

_Where the sector's activity concentrated this window._

| Sub-sector | Events |
|---|---|
| [grid storage] | [7] |
| ... top 8 rows from the digest's `aggregates.sub_sector` ... |

(Render only if ≥1 sub-sector value is present; take the rows from the
digest — do not count events yourself.)

---

## Regulation & policy — [m] web pages scanned · [n] events found

| Event | Sub-sector | Date | Stage | Authority | Sources |
|---|---|---|---|---|---|
| [event title, ≤100 chars] | [offshore wind] | [Jul·12] | [Enacted] | [European Commission] | [domain] + [k] others |
| [≤10 rows, or the empty-table pattern if n=0] |

([n-10] more in the full dataset)

---

## Technology & product — [m] web pages scanned · [n] events found

| Event | Company | Sub-sector | Date | Type | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## Demand & commercial — [m] web pages scanned · [n] events found

| Event | Company | Sub-sector | Date | Type | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## Capacity & footprint — [m] web pages scanned · [n] events found

| Event | Company | Sub-sector | Date | Type | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## [n] events worth watching

_Developing situations — rumored, in talks, or filed and not yet decided._

| Event | Company | Category | Sub-sector | Date | Sources |
|---|---|---|---|---|---|
| [event title, ≤100 chars] | [Company] | [Capacity & footprint] | [nuclear power] | [Jul·18] | [domain] + [k] others |
| ... up to 10 rows ... |

(K more — filter on `is_developing` in the full dataset)

(Render only if ≥1 event qualifies.)

---

## Analysis
[At most two factual bullets — see § Analysis.]

_Capital view — funding and M&A for this sector: ask for the **VC pack**._

[Paste the **More with CatchAll** footer verbatim from
`references/NEXT-STEPS.md` — the `---` rule, the `## More with
CatchAll` heading, and the link line (default footer — this is not a
watchlist run). Never type the URLs from memory.]
```

### Events worth watching — selection rule

Forward-looking situations the user can act on before they resolve.
Mechanical — same data in, same rows out:

1. Start from all events where `is_developing == true`.
2. Dedup by title across categories (keep the most-cited copy).
3. **Sort by date, most recent first** (undated events last, then by
   citation count). This is the one section that does **not** sort by
   citation count: the category tables above are already ranked that
   way, so re-ranking the same events by coverage would just replay
   them. Ordered by date it answers a different question — what surfaced
   most recently, which is where a developing situation is most likely
   to move next.
4. Top 10; the `Category` column is the originating category's display
   name.

Render only if ≥1 event qualifies. If more than 10 qualify, append
`(K more — filter on \`is_developing\` in the full dataset)`. Not
counted toward "Total events found" — it is forward-looking by
definition.

### Analysis

At most two factual bullets, each adding something the tables don't
already show. Use display names (Regulation & policy, Capacity &
footprint), never JSON keys. No strategy, no recommendations, no
editorializing. Omit a bullet rather than pad.

### Output discipline

The output renders what CatchAll returns. Follow the canonical rules in
full — `OUTPUT-REPORT.md` § No agent-written caveats and
`JOB-LIFECYCLE.md` § No narrating the machinery. Skill-specific point:
**At a glance and Events worth watching are mechanical filters, not verdicts**
— a row is there because it matched the rule, and the cells are the
matched facts; no trend calls, no "the sector is heating up"
commentary. Operational issues go to `meta.run_flags[]` in the JSON,
never to chat.

## Length discipline

- Dashboard + At a glance: a few lines, mostly numbers
- Each category section: ≤10 events in chat, rest in the full dataset
- Zero-event sections: render the empty-table pattern (do not omit)
- Events worth watching: ≤10 rows, only if any qualify
- Analysis: at most two factual bullets

## Handling edge cases

| Scenario | Action |
|---|---|
| Quiet window (most categories zero) | Render each zero-event category with the empty-table pattern. A quiet sector is a positive result. |
| One company dominates the news | Expected — it surfaces across several categories. Do not suppress it. |
| One sub-sector dominates | Expected — At a glance shows the concentration. Render as-is. |
| An event fits two categories | Render it in each category CatchAll returned it under; do not move or dedup across category tables. (Spotlights dedup per their rules.) |
| Very broad sector ("technology") | Run as given — do not narrow the scope yourself. |

## What this skill does NOT do

- Does not track a named company list — that is competitor-snapshot-catchall
  (competitors) or portfolio-monitoring-catchall (holdings).
- Does not deep-dive capital activity — funding-only is fundraising-catchall,
  M&A-only is mergers-and-acquisitions-catchall, both together is vc-pack-catchall.
- Does not produce market sizing, forecasts, or survey data — it
  surfaces reported events; the reader judges the trend.
- Does not set up ongoing monitoring — one-shot brief. If the user
  wants recurring coverage, suggest converting the four searches into a
  CatchAll monitor.
