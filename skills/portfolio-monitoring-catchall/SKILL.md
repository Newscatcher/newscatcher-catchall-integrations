---
name: portfolio-monitoring
description: Use this skill when an investor wants to know what has happened across the companies they hold — a portfolio monitoring brief over a list of portfolio companies. Triggers on "what's happening across my portfolio", "portfolio monitoring brief", "monitor my portfolio companies", "any of my companies in trouble", "pull signals on my portfolio companies", "portfolio update for the last [period]", "give me a read on my book of companies". Takes a company list named in text or uploaded as a CSV with name and domain columns, and scans it for capital and exit events, distress and downside risk, leadership and governance changes, and commercial momentum in one run. Do not use for a single competitor's strategic moves, for funding-only or M&A-only market scans, or for ESG, vendor, or customer-account risk.
---

# Portfolio Monitoring

Produces a structured brief of the most material developments across an
investor's portfolio companies, in four categories investors act on:
**capital and exits, distress and risk, leadership and governance, and
commercial momentum**. Runs on a list of up to 100 companies (named in
text or uploaded as a CSV) via CatchAll's watchlist mode, and leads with
two cross-cutting views: **Early Warnings** (the companies showing
downside signals) and **Events worth watching** (developing situations).

## When to use

The user holds or tracks a set of companies and wants to know what
changed across all of them. Triggers:

- "What's happening across my portfolio this month"
- "Run a portfolio monitoring brief on these companies"
- "Any of my portfolio companies in trouble"
- "Pull signals on my portfolio for the last [period]"
- "Give me a read on my book of companies"

For a single competitor's strategic moves, use competitor-snapshot. For
a market-wide funding or M&A scan not tied to a held list, use the
fundraising or mergers-and-acquisitions skills.

## Inputs to confirm before running

Follow `references/QUERY-REVIEW.md` for the general intake rules.
Skill-specific specifics:

1. **Portfolio** (required) — a company list in one of two forms:
   - **Text-named**: company names in the user's message.
   - **Uploaded CSV/spreadsheet**: a file with at minimum a `name`
     column; `domain` strongly preferred. See
     `references/COMPANY-WATCHLIST.md` for domain handling.
2. **Time window** — ask if not specified. Portfolio events are sparse
   and the natural cadence is monthly, so the **waive-off default is the
   last 30 days** (not 7).
3. **Max results** — ask via the picker, combined with the time-window
   question in the same step; skip if the user already named a number.
   Header: `Max results`. Question: `How many results at most? Limits the
   number of validated results returned per search.` Options — labels
   only, empty descriptions, in this order: **`50 (Recommended)`**, `10`,
   `100`, `All`. The chosen number is each search's `limit`.
4. **Specific angle** (optional) — if the user flags a focus ("just the
   distressed ones"), still run all four searches; the matching spotlight
   leads.

Special-case rules:
- **List of 101+ companies**: tell the user the skill caps at 100, ask
  whether to proceed with the first 100, and point them to the CatchAll
  platform + Book a demo links (`references/NEXT-STEPS.md`) for larger
  lists.
- **Ambiguous name**: if a company name could refer to multiple things,
  ask one clarifying question before submitting.

## How the skill runs

**One execution path: always watchlist mode.** A list builds a watchlist
of N; a single named company builds a watchlist of 1 (no upload prompt),
so every event carries `ed_score`, `relation`, and `is_developing`
regardless of list size.

The full watchlist mechanics — building the company list, domain
handling, the 100-company cap, building the dataset, submitting with
`connected_dataset_ids`, polling, and parsing `connected_entities` — are
in `references/COMPANY-WATCHLIST.md`. Follow it verbatim; do not write a
helper script.

Skill-specific details:
- Dataset name slug: `portfolio-monitoring`
- Run all four bucket queries below in their watchlist phrasing,
  connected to the dataset, with each bucket's own `enrichments` plus the
  cross-cutting `is_developing` enrichment.
- Attribute each event to its highest-`ed_score` company in
  `connected_entities`; that name populates the `company` field.
- Surface in chat only events whose attributed company scores
  `ed_score >= 8` (`COMPANY-WATCHLIST.md` Step 4); those count toward
  "events found". Lower-scored events go to the downloads only.

### Load more

Each bucket's `limit` is the number chosen in the `Max results` picker.
If any bucket hits that cap (`valid_records == limit`), add a short note
under that bucket's table: `Showing [limit] of [N estimated]. Ask to
load more.` On request, call `continue_job` with a higher limit, repoll
to terminal, re-pull all pages, and regenerate the xlsx, JSON, and CSV
atomically.

## Bucket queries

Run CatchAll for each of the four buckets below. In watchlist mode the
query omits company names — `connected_dataset_ids` scopes the search to
the list.

> **Before submitting any jobs**, read `references/QUERY-REVIEW.md`
> (when to confirm scope vs. proceed), then
> `references/COMPANY-WATCHLIST.md` (build the list, batch-create
> entities, the dataset, connected submits, attribution — every run uses
> it), then `references/JOB-LIFECYCLE.md` (per-search contract) and
> `references/CONCURRENCY.md` (the multi-search layer: waves, the live
> progress table, checkpoints, no time cap, re-poll on follow-up). Follow
> all four verbatim. The progress table uses one row per search; the same
> rows persist across every checkpoint with status emojis and live counts
> updating in place.

> **Before writing output**, read `references/OUTPUT-REPORT.md` (xlsx +
> JSON + CSV contract: file naming, schema, columns, the `Full dataset:`
> block, the spotlight slot, vocabulary, dates) and
> `references/NEXT-STEPS.md` (the **More with CatchAll** footer).

Submit in concurrency-sized waves (`references/CONCURRENCY.md`). **Each
bucket is an independent CatchAll search.** Some events plausibly fit two
buckets (an acquisition that is also an exit); render each bucket's
results as CatchAll returned them — do not move events between buckets
after pull. "Bucket" and "wave" are implementation words; they never
appear in user-facing text. A unit of work is a **search**.

### Cross-cutting enrichment (every bucket)

Add this to every bucket's `enrichments` array alongside the
bucket-specific fields. It powers the **Events worth watching** spotlight:

- `is_developing` (option, values: `true | false`): "True ONLY if the
  event is not yet finalized: (1) RUMORED or REPORTEDLY happening — not
  officially confirmed; (2) IN ACTIVE NEGOTIATION with the outcome not
  finalized (e.g. 'in talks to be acquired', term sheet circulating);
  (3) officially announced with a SPECIFIC FUTURE effective date not yet
  arrived (e.g. 'IPO expected Q3', 'CEO joins August 1', 'layoffs take
  effect next quarter'); or (4) a FILED-BUT-NOT-CLOSED step (e.g. S-1
  filed and not yet priced, WARN notice filed ahead of layoffs). False
  for completed, already-effective events, earnings results, and ongoing
  trends. When in doubt, default to false."

### 1. Capital & exits

- **Watchlist query**: `Funding rounds, valuation changes, venture debt, secondary sales, IPOs and direct listings, and acquisitions or buyouts of companies in this watchlist in the last [window]`

Enrichments:
- `event_type` (option, values: `round | bridge | debt | secondary | grant | ipo | acquired`): "The kind of capital or liquidity event"
- `direction` (option, values: `up | down | flat | exit | neutral`): "Valuation direction. up = up round or markup; down = down round, markdown, or rescue/emergency financing; flat = flat round; exit = acquisition of the company or IPO; neutral = not applicable or undisclosed"
- `amount` (number): "Capital raised or deal value in USD; null if undisclosed"
- `valuation` (text): "Reported valuation with basis, e.g. '$1.4B post-money'; null if undisclosed"
- `counterparty` (company): "The other party to the event — lead investor, lender, acquirer, or buyer. A different company than the portfolio company the event is about; null if there is no counterparty (e.g. an IPO or an undisclosed raise)."

### 2. Distress & risk

- **Watchlist query**: `Layoffs, restructuring, bankruptcy or insolvency, defaults and covenant breaches, going-concern warnings, office or product-line closures, distressed sales, and major lawsuits or regulatory actions involving companies in this watchlist in the last [window]`

Enrichments:
- `signal_type` (option, values: `layoffs | restructuring | bankruptcy | default | going_concern | closure | distressed_sale | litigation | regulatory`): "The kind of distress or downside signal"
- `scale` (text): "Magnitude where stated, e.g. '~600 roles', '3 offices', '$120M facility'; null otherwise"
- `authority` (text): "The court, regulator, or body involved where applicable, e.g. 'US Bankruptcy Court (Del.)', 'SEC', 'CMA'; null otherwise"

### 3. Leadership & governance

- **Watchlist query**: `Founder and executive departures, C-suite and senior leadership hires, and board or governance changes at companies in this watchlist in the last [window]`

Enrichments:
- `executive_name` (text): "Name of the executive or board member"
- `role` (text): "Role or title, e.g. CEO, CFO, Head of AI"
- `move_type` (option, values: `hire | departure | promotion | board_change`): "Type of leadership or governance move"

### 4. Commercial momentum

- **Watchlist query**: `Acquisitions made by companies in this watchlist, major product launches, notable customer wins and contracts, strategic partnerships and integrations, and geographic or market expansion in the last [window]`

Enrichments:
- `event_type` (option, values: `add_on_acquisition | launch | customer_win | partnership | expansion | clearance`): "The kind of commercial or growth event"
- `counterparty` (company): "The other party to the event — the acquired company, named customer, or partner. A different company than the portfolio company the event is about; null if there is no counterparty (e.g. a product launch or internal expansion)."

## Output

Every run produces four deliverables: a markdown chat response, an xlsx
workbook, a JSON file, and a CSV file. See `references/OUTPUT-REPORT.md`
for file naming, sheet/column structure, schema, vocabulary, date
formatting, the spotlight slot, and the zero-event pattern. Slug:
`<portfolio-slug>-portfolio-monitoring` (e.g.
`acme-ventures-portfolio-monitoring`); if the user gives no portfolio
name, use `portfolio-monitoring`.

The chat response is a compressed brief; full enumeration lives in the
xlsx, JSON, and CSV. Lead with the dataset.

### Per-bucket table columns

All bucket tables share **Event** first and **Sources** last, with a
**Company** column immediately after Event (from `connected_entities`).
The middle columns are bucket-specific:

| Bucket | Middle columns |
|---|---|
| Capital & exits | Type, Amount |
| Distress & risk | Signal, Scale |
| Leadership & governance | Person, Move |
| Commercial momentum | Type, Counterparty |

If an enrichment is missing, render the cell as `—`. Do not add an
`ed_score` or `relation` column — chat shows only `ed_score >= 8` events;
the scoring never appears. **Event titles**: truncate to ~100 characters
(append `…`). **Date cells**: short form `May 16` with a non-breaking
space (U+00A0).

### Chat response

Lead with the dashboard panel + at-a-glance, then the four bucket
sections, then the two spotlights, then Analysis, then the footer.

```
# [Portfolio name] — Portfolio Monitoring

Full dataset:
  xlsx: [absolute path to .xlsx]
  JSON: [absolute path to .json]
  CSV:  [absolute path to .csv]

## CatchAll findings

| Watchlist | Companies | Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|---|---|
| [name] | [N] | [Apr 23 – May 23, 2026] | [May 23, 2026] | Base | **[M]** | **[N]** |

---

## At a glance

| Company | Events found |
|---|---|
| [Company] | [n] |
| ... |

---

## Capital & exits — [m] web pages scanned · [n] events found

| Event | Company | Date | Type | Amount | Sources |
|---|---|---|---|---|---|
| [event title, ≤100 chars] | [Company] | [May·12] | [Up round] | [$120M] | [domain] + [k] others |
| [≤10 rows, or empty-table pattern if n=0] |

([n-10] more in the full dataset)

---

## Distress & risk — [m] web pages scanned · [n] events found

| Event | Company | Date | Signal | Scale | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## Leadership & governance — [m] web pages scanned · [n] events found

| Event | Company | Date | Person | Move | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## Commercial momentum — [m] web pages scanned · [n] events found

| Event | Company | Date | Type | Counterparty | Sources |
|---|---|---|---|---|---|
| [≤10 rows or empty-table pattern] |

---

## Early Warnings — [window label]

_Companies showing downside signals this window._

| Company | Signals this window | Latest | Sources |
|---|---|---|---|
| [Company] | [Signal (key fact) · Signal (key fact) · …] | [May·18] | [domain] + [k] others |
| ... up to 10 rows ... |

(K more in the full dataset)

(Render only if ≥1 company qualifies — see § Early Warnings — selection rule.)

---

## [n] events worth watching

_Developing situations — rumored, in-talks, filed, or planned._

| Event | Company | Category | Date | Sources |
|---|---|---|---|---|
| [event title, ≤100 chars] | [Company] | [Capital & exits] | [May·17] | [domain] + [k] others |
| ... up to 10 rows ... |

(K more — filter on `is_developing` in the full dataset)

(Render only if ≥1 event qualifies.)

---

## Analysis
[At most two factual bullets — see § Analysis.]

[Paste the **More with CatchAll** footer verbatim from `references/NEXT-STEPS.md` — the `---` rule, the `## More with CatchAll` heading, and the link line (watchlist link on watchlist runs only). Never type the URLs from memory.]
```

Single-company runs (watchlist-of-1) drop the Company column and the
at-a-glance table; everything else is unchanged. The footer follows
`references/NEXT-STEPS.md` and includes the Company Watchlists link
(every run is a watchlist run).

### Early Warnings — selection rule

The signature spotlight: the companies an investor should look at first.
Mechanical — same data in, same rows out:

1. **Flag** every company with ≥1 event where `bucket == distress` **OR**
   (`bucket == capital` AND `direction == down`), at `ed_score >= 8`.
2. For each flagged company, its **signals** are all those qualifying
   events, **plus** any leadership **departures**
   (`move_type == departure`, `ed_score >= 8`) the same window — for an
   already-flagged company an exec exit reads as part of the picture.
3. Render each signal as a chip `<label> (<key fact>)` — label from
   `signal_type` (or `Down round` for a capital-down event, `Departure`
   for a leadership exit); key fact from `scale` / `amount` / `valuation`
   / `role`. **List every signal** — never show one and drop the rest.
4. **Severity** per company = the highest tier among its distress /
   capital-down signals: **terminal** = `bankruptcy, default,
   going_concern, distressed_sale`; **acute** = everything else
   qualifying. (Leadership departures don't change the tier.)
5. Sort by severity (terminal first), then by total citation count
   descending. `Latest` = the most recent signal's date; `Sources` = the
   most-cited signal's citations.
6. One row **per company**; cap at 10; append `(K more in the full
   dataset)` if more qualify.
7. Render only if ≥1 company qualifies; no empty-table pattern.

In the xlsx this spotlight is **one row per event** (per
`OUTPUT-REPORT.md`). Emit `meta.spotlights[].columns` in this order:
`company, signal, severity, title, date, detail, citation_count,
citations, summary`. `company, title, date, citation_count, citations,
summary` are base fields (the script fills them from the event); `signal`
(the signal type), `severity` (the tier), and `detail` (the single key
fact — amount, scale, or role) are extra columns you supply on each
membership row.

### Events worth watching — selection rule

Forward-looking situations the user can act on before they complete.
Mechanical:

1. Start from all events where `is_developing == true`.
2. Filter `ed_score >= 8`.
3. Dedup by title across buckets (keep the highest-scored).
4. Sort by citation count descending.
5. Top 10; the `Category` column is the originating bucket's display name.

In the xlsx, emit `meta.spotlights[].columns`: `company, category, title,
date, citation_count, citations, summary` — `category` (the bucket display
name) is the one extra column, supplied on each membership row.

Render only if ≥1 event qualifies. If more than 10 qualify, append
`(K more — filter on \`is_developing\` in the full dataset)`. Not counted
toward "Total events found" — it is forward-looking by definition.

### Analysis

At most two factual bullets, each adding something the tables don't
already show. Use display names (Capital & exits, Distress & risk), never
JSON keys. No strategy, no recommendations, no editorializing. Omit a
bullet rather than pad.

### Output discipline

The output renders what CatchAll returns. Follow the canonical rules in
full — `OUTPUT-REPORT.md` § No agent-written caveats and
`JOB-LIFECYCLE.md` § No narrating the machinery. Skill-specific point:
**Early Warnings is a mechanical filter, not a verdict.** A company is
listed because a downside event matched the rule, and the signal chips
are the matched facts — no colours, no risk scores, no "needs
intervention" commentary. Operational issues go to `meta.run_flags[]` in
the JSON, never to chat.

## Length discipline

- Dashboard + at-a-glance: a few lines, mostly numbers
- Each bucket section: ≤10 events in chat, rest in the full dataset
- Zero-event sections: render the empty-table pattern (do not omit)
- Early Warnings / Events worth watching: ≤10 rows each, only if any qualify
- Analysis: at most two factual bullets

## Handling edge cases

| Scenario | Action |
|---|---|
| Quiet window (most buckets zero) | Render each zero-event bucket with the empty-table pattern. Early Warnings simply doesn't render — a quiet portfolio is a positive result. |
| One company dominates the news | Expected — it surfaces across buckets and leads Early Warnings. Do not suppress it. |
| A company was just acquired or shut down | It appears under Capital & exits (exit) or Distress & risk (terminal). Lead Early Warnings with the terminal cases. |
| Mixed stages (seed to growth) in one list | Render as-is; do not normalize across stages. |
| A private company with thin coverage | Its zero counts are honest; no commentary needed. |

## What this skill does NOT do

- Does not cover ESG, reputational, vendor, or customer-account risk — those are separate skills.
- Does not give investment advice, valuation marks, or buy/sell calls — it surfaces public signals; the investor judges.
- Does not pull internal metrics (ARR, burn, board decks) — public signals only.
- Does not set up ongoing monitoring — one-shot brief. If the user wants recurring coverage, suggest converting the four searches into a CatchAll monitor.
