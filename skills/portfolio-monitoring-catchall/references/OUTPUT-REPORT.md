# Output Report Reference

Each run produces four deliverables: a markdown chat
response, an xlsx workbook, a JSON file, and a CSV file. The chat
response is a **multi-section report** — one section per search category,
each with its own table. The xlsx is the human-review artifact (open
in Excel/Sheets); the JSON is the pipeline artifact; the CSV is the
lightweight tabular interchange format. This file defines the contract
for the downloadable artifacts and the link rendering. Per-skill content
design (the section/category names, what fields appear in each table)
lives in the skill's `SKILL.md`.

## Files produced

Every run produces, at minimum:

| Filename | Purpose | Audience |
|---|---|---|
| `<slug>.xlsx` | Multi-sheet styled workbook (Overview, Run info, spotlight sheet(s) where applicable, one sheet per bucket, Citations sheet with clickable URLs) | Humans opening in Excel / Google Sheets |
| `<slug>.json` | Full hierarchical dataset with metadata. Pipeline-native | Scripting / programmatic ingestion |
| `<slug>.csv` | Flattened tabular view, one row per event | Tools that don't speak JSON (BI, R, pandas, Numbers) |

Where `<slug>` is `<entity-or-topic-slug>-<skill-name>`, lowercase, hyphenated,
dropping the skill name's `-catchall` suffix. Examples:

- `atlassian-competitor-snapshot.xlsx` / `.json` / `.csv`
- `apple-supply-chain.xlsx` / `.json` / `.csv`
- `pharma-ma-deals.xlsx` / `.json` / `.csv`

Save all three files to the current working directory unless the user
specifies otherwise. **You do not hand-build them** — `scripts/build_report.py`
renders the xlsx, JSON, and CSV deterministically (the workbook is never
authored by hand, and footer links come from `references/links.json`, so no
data or URL is reconstructed at runtime). Pass `--watchlist` on watchlist-mode
runs so the footer includes the Company Watchlists link. (Run `pip install
openpyxl --break-system-packages` first if openpyxl is missing.)

Both ways populate a `raw/` dir of verbatim per-bucket pulls and then run the
**same** renderer (`build_report.py --raw-dir`). They differ only in who writes
`raw/`: the **API path** (a script fetches it) or the **MCP path** (you save
each pull as it comes back). **Try the API path first; fall back to the MCP path
when the environment can't use it.** The fallback is automatic — a non-zero exit
signals it — and **silent: never mention which path ran in chat.**

### API path (preferred)

Once every bucket job has completed, fetch the full results straight to disk.
**Run this directly — do not check whether an API key exists first.** The script
resolves the key itself (env / `.env` / MCP config) and signals the outcome by
its exit code.

```
scripts/catchall_api.py --out-dir raw --bucket <bucket_key>=<job_id> [--bucket …]
```

one `--bucket` per bucket, mapping each bucket key to its completed `job_id`. It
writes `raw/<bucket>.json` (the verbatim pull for each bucket) and prints a
**compact digest** — the per-event lines (with `record_id`s) you read to choose
spotlights and fill the manifest.

- **On exit 0**, write `manifest.json` into that same dir (shape below), then:

  ```
  scripts/build_report.py --raw-dir raw --slug <slug> [--watchlist]
  ```

  The script reads every event field from the raw pulls, so you transcribe no
  event data — the manifest carries only run meta and the spotlight picks.

- **On a non-zero exit** (no API key, or the API is unreachable — the normal
  case on claude.ai / ChatGPT), take the **MCP path** below: pull with MCP, save
  each result to `raw/` yourself, then run the same `--raw-dir` render.

`manifest.json` (both paths write this — run meta + spotlight picks, no event data):

```json
{
  "meta": { "entity": "…", "window": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"},
            "prepared_at": "<ISO 8601 UTC>", "skill": "…", "mode": "base",
            "company_count": "<N — watchlist runs>",
            "aggregate_counts": ["<enrichment name — optional>"] },
  "bucket_order": ["<bucket_key>", "…"],
  "spotlights_meta": [ { "key":"…", "name":"…", "subtitle":"…", "columns":[…] } ],
  "spotlights": { "<key>": [ { "record_id":"<from the digest>", "<extra col>":"<value>" } ] }
}
```

`bucket_order` lists the buckets in render order; each name matches a
`raw/<bucket>.json`. `spotlights_meta` and `spotlights` are exactly `meta.spotlights`
and the top-level `spotlights` of the JSON shape below — except membership
references the raw **`record_id`** (from the digest) instead of `event_id`, and
carries only the non-base columns. Titles, dates, summaries, citations, and
watchlist attribution all come from the raw records. (On watchlist runs the
summary is the entity relation; a non-watchlist skill defines a `summary`
enrichment instead — the builder maps it into each event's summary and drops
it from the enrichment columns.)

### MCP path (fallback — works on every platform)

Pull each bucket's completed job with the MCP `pull_results` tool and **save its
result to `raw/<bucket>.json` exactly as it comes back** — the pull response is
already the shape `--raw-dir` reads. If your environment already wrote a pull to
a file (large results often land on disk), use that file directly. Then write
`manifest.json` (above) and run the same renderer:

```
scripts/build_report.py --raw-dir raw --slug <slug> [--watchlist]
```

**Do this mechanically — one write per bucket, no deliberation.** Never reshape
the pull, never trim or pick "representative" citations, never count them, never
write a script to encode records or URLs. The pull is already correct and
complete; copying it verbatim is the whole job, and the renderer extracts every
field. A large citation list is not a problem to solve — save it as-is and move
on.

## Writing the chat from the digest

`build_report.py` writes a **chat digest** to `raw/digest.json` —
the dashboard numbers, each bucket's events (already sorted, each with a prebuilt
`sources` string and its enrichment values), and every spotlight with its rows
**resolved**. **Read `raw/digest.json` and build the chat report from it. It is
authoritative — do not recompute anything, and do not re-open the JSON/CSV to
pull table rows or resolve spotlight ids.** Every value you need is already
there, so you write no ad-hoc extraction code. If the manifest's meta lists
`aggregate_counts`, the digest adds `aggregates.<field>` — that enrichment's
value counts across all events, sorted by count — read per-value totals from
it rather than counting rows.

## The "Full dataset" block

The chat output begins with a `Full dataset:` block, immediately after
the title — three absolute file paths in plain text, in xlsx → JSON →
CSV order (xlsx first because it's the most-used deliverable for
human readers):

```
Full dataset:
  xlsx: /path/to/working-dir/atlassian-competitor-snapshot.xlsx
  JSON: /path/to/working-dir/atlassian-competitor-snapshot.json
  CSV:  /path/to/working-dir/atlassian-competitor-snapshot.csv
```

Notes:

- Label it **`Full dataset:`** — not "Files saved", not "Downloads".
  "Full dataset" tells the reader *what* the files are (the complete
  result set) rather than narrating a file-write.
- **No "how to open" tip line.** Don't add cmd+click / `open <path>`
  instructions — the paths are self-explanatory and the extra line is
  noise.
- Use **absolute paths** (resolved from the working directory at run
  time), not relative. xlsx first, then JSON, then CSV. Two-space indent.
- Elsewhere in the chat, refer to these as the **full dataset** — e.g.
  "(12 more in the full dataset)" — never "the download".

Never embed file contents in the chat output. The artifact is the
artifact; the chat references it.

## Vocabulary

Use accessible language in chat output. Reserve technical CatchAll API
terms (validators, candidates, enrichments) for JSON/CSV column names
and developer documentation.

| Chat output | API / JSON term |
|---|---|
| "web pages scanned" | candidates / progress_validated |
| "events found" | valid_records |
| "sources" | citations |

Use "events found" consistently across all skills and all buckets. Stick
with "events."

JSON/CSV columns stay technical (`event_title`, `event_date`, `citations`)
for pipeline consistency.

## Top-of-output dashboard panel

The run-level metrics (window, prepared date, total web pages scanned,
total events found) appear in a dashboard table at the top of every
chat response, immediately after the `Full dataset:` block. It must draw the eye, not
drown in body text.

Use a `## CatchAll findings` header followed by a horizontal markdown
table with numbers bolded. Column labels use "Total …" for aggregable
counts to distinguish dashboard totals from per-bucket numbers later:

```
## CatchAll findings

| Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|
| May 13–20, 2026 | May 20, 2026 | Base | **61,007** | **8** |
```

The `Mode` cell is `Base` for full-pipeline runs (the default) or
`Lite` for lighter retrieval. Mode is also in `meta.mode` in the JSON;
surfacing it in chat tells the user which configuration produced the
result, useful if they later go into the CatchAll UI to reproduce or
extend the search.

Per-event source attribution lives in the Sources column of each
bucket's event table — no aggregate "unique sources" count in the
dashboard. The aggregate is ambiguous (could be misread as "CatchAll
only checked N sources") and adds little over the per-event view.

Tables render visually in Claude Code, Cursor, claude.ai, and most
markdown UIs. This panel is **non-negotiable**.

## Dates

Use friendly, unambiguous dates in chat output:

- **Date ranges (window header)**: `May 13–20, 2026` (en-dash). Always
  include the year.
- **Single dates in body text or section headers**: `May 16, 2026`
  with the year.
- **Single dates inside table cells**: use the short form `May 16`
  (no year), and join the month and day with a **non-breaking space**
  (U+00A0) — `May⍽16` — so the date never wraps to two lines in a
  narrow column. A regular space lets the renderer break "May 16" into
  "May" / "16" across two lines, which looks broken. The year is
  carried by the window header — context is preserved.
- Never use ISO `2026-05-13` in chat — it parses fine but reads as a
  number, not a date, and `05-13` is ambiguous to non-ISO readers.

If a query window spans multiple years, override the table-cell short
form and include the year in cells too (`May 16, 2025` and `Jan 10, 2026`
in the same table need disambiguation).

JSON/CSV columns keep ISO format (`YYYY-MM-DD`) for pipeline compatibility.

## Tables for event lists

When a bucket has 1+ events, render them as a markdown table — not as
bullets. Tables emphasize that the output is structured data. Bullets
read as narrative summary.

**Row order** — sort events by **citation count, descending** (most-
covered first). Citation count is the most-covered proxy for "story
importance" and is the same axis the reader is reading in the Sources
column, so the table reads top-down from biggest story to smallest. This
sort applies to every bucket table and to any cross-cutting section
(e.g. a spotlight section), so the reader can compare across
sections without re-orienting.

Default columns:

| Column | Notes |
|---|---|
| Event | Truncate event title to ~100 chars; append `…` if truncated. ~100 leaves room for a complete phrase — shorter limits cut titles mid-thought. |
| Date | Friendly short form with a non-breaking space (per § Dates) |
| Sources | First citation domain + count of others: `smartkarma.com + 2 others`. Use "others" not "more" — "more" is ambiguous about what. |

Per-skill enrichment columns can be appended after Sources.

When a bucket has 0 events, do not render an empty table. See the
zero-event pattern below.

## Zero-event sections

A zero-event section is a positive result — it tells the reader nothing
qualifying happened in the window, and the article-count backs that
claim. The section must take visual space so it doesn't disappear: show
the table header (the data shape this bucket would have produced) plus
a single empty row stating no events were found.

```
## M&A and capital — 33,250 web pages scanned · 0 events found

| Event | Date | Target | Deal value | Sources |
|---|---|---|---|---|
| _No events found in this window._ |  |  |  |  |
```

Why the empty table:

- Shows the **data shape** — the reader sees what columns this bucket
  would have produced.
- **Takes space** — the section sits visually alongside non-empty
  sections rather than collapsing to a single line.
- Confirms **coverage** — `33,250 web pages scanned` is right there in
  the header, no ambiguity about whether the bucket was really searched.

Use exactly `_No events found in this window._` in the first cell.
**Leave the other cells blank — do not use em-dashes.** Em-dashes
imply "no data found for this specific field," which is wrong: the
whole row doesn't exist. Blank cells read as intentionally empty.

**Do not add commentary about what the candidate noise was.** The user
trusts the recall number and doesn't need a justification tour.

## No agent-written caveats

CatchAll does not return warnings or validator-confidence flags. Do
not have the agent add its own caveats, footnotes, or validator
second-guessing to the output. The skill renders the raw API result as-is.
If CatchAll's validator misattributes an event (e.g., catches the wrong
company), that fact stays in the data — the user evaluates the raw
output and forms their own judgment, as they would when calling CatchAll
directly.

(If CatchAll ever adds API-level warnings, those can be surfaced — but
only API-returned content, not agent analysis.)

## Spotlight sections (cross-cutting highlights)

A report may end with one or two **spotlight** sections — cross-cutting
tables that re-surface a mechanically selected slice of the full result
set to answer, at a glance, the question the reader most wants answered.
The skill's `SKILL.md` defines each spotlight's name, selection rule,
grain, and columns; this file defines only the slot. Emit the selection as the
manifest's `spotlights` (membership by `record_id` + extra-column values, per
§ API path) — `build_report.py` resolves and renders it; never hand-build a
spotlight table.

- **Placement.** Chat: after the last bucket section, before Analysis,
  separated by a `---` rule. xlsx: one sheet per spotlight, after Run
  info and before the per-bucket sheets.
- **Mechanical, never editorial.** Selection is a deterministic filter
  and sort over the data — same data in, same rows out. No agent
  judgment, no commentary, no flags, colours, or scores the agent
  invents. A row is there because it matched the rule; the columns are
  the matched facts.
- **Render only when ≥1 row qualifies.** Unlike a bucket, a spotlight has
  no empty-table pattern — the absence of qualifying events is not itself
  a finding to show.
- **Sort** by citation count descending by default (matches the bucket
  tables); a spotlight may set its own sort key (e.g. a severity tier, a
  date). Apply that sort when you build the membership list — the
  renderer preserves the order you emit and never re-sorts it.
- **Cap** at 10 rows in chat by default; if more qualify, append one
  trailing `(K more — … in the full dataset)` line.
- **Grain is the spotlight's choice** — one row per **event** (e.g. a
  forward-looking view) or one row per **entity** (e.g. a per-company
  roll-up). When a per-entity row aggregates several events, **every
  contributing signal stays visible in that row** — never show one and
  drop the rest.
- **In the xlsx a spotlight is always one row per event**, even when the
  chat renders it per-entity — so the sheet stays filterable and complete
  (filter to one entity for all its events, or by a signal column to see
  that signal across the set).

## Section ordering and integrity

These rules prevent the most common rendering bugs:

- **Render every bucket section in the exact order defined by the
  skill, every time.** Do not skip a section because it's empty —
  zero-event sections still get the dashboard panel + empty table.
- **Each section's table belongs to that section only.** Do not
  borrow rows from another bucket. If a bucket has 0 events, render
  the empty-table pattern; do not fill its rows with events from a
  later bucket.
- **Render each bucket's table exactly once.** No duplicated tables,
  no repeated headers.
- **Insert a horizontal rule (`---`) between every section**, on its
  own line after the prior section's last line and before the next
  section's `##` header. A blank line alone collapses to minimal space
  in most renderers; the rule draws a thin line with padding, giving
  the eye a clear break.

## JSON shape

This is the `<slug>.json` artifact **`build_report.py` emits** — reference, not a
build recipe. You never author it (you write the small `manifest.json` above);
it's shown here because the manifest's `spotlights` reuse its spotlight schema.

Every JSON artifact has the same top-level structure:

```json
{
  "meta": {
    "entity": "<company name | topic | watchlist name>",
    "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
    "prepared_at": "<ISO 8601 UTC>",
    "skill": "<skill name>",
    "mode": "base",
    "recall": {
      "total_candidates_scanned": 24847,
      "total_validated_events": 14,
      "unique_sources": 247
    },
    "per_bucket": {
      "<bucket_key>": {
        "job_id": "<UUID returned from submit_query for this bucket's job>",
        "candidates_scanned": 312,
        "validated_events": 2
      }
    },
    "spotlights": [
      { "key": "<spotlight_key>", "name": "<sheet name>", "subtitle": "<italic caption>", "columns": ["<ordered column list: base event fields + extras like signal/severity>"] }
    ]
  },
  "events": {
    "<bucket_key>": [
      {
        "id": "<unique within the run, e.g. capital_exits_1>",
        "title": "<event title>",
        "date": "<YYYY-MM-DD | null>",
        "summary": "<1-2 sentence factual summary>",
        "citations": [
          { "source": "<domain>", "url": "<full URL>", "published_date": "<YYYY-MM-DD | null>" }
        ],
        "enrichments": { "<custom field>": "<value>" }
      }
    ]
  },
  "spotlights": {
    "<spotlight_key>": [
      { "event_id": "<id of an event above>", "<extra column>": "<value the rule assigns>" }
    ]
  }
}
```

**Required keys per event**: `id`, `title`, `date`, `summary`, `citations`.
Each `id` is unique within the run (e.g. `<bucket>_<n>`) so spotlights can
reference events without repeating their data.

**Spotlights are data, not re-typed events.** `meta.spotlights` declares each
spotlight: its `key`, sheet `name`, italic `subtitle`, and `columns` — **the
full ordered column list for the sheet**. Base event fields in that list
(`company`, `title`, `date`, `citation_count`, `citations`, `summary`,
`ed_score`, `relation`) are pulled from the referenced event; any other column
(e.g. `signal`, `severity`) takes its value from the membership row. The
top-level `spotlights` object maps each key to the events it selects — **by
`event_id`**, plus values for the non-base columns. Apply the spotlight's
selection rule (in the skill's `SKILL.md`) to choose the ids; never copy an
event's title/summary/etc. into the membership row — `build_report.py` pulls
those from the referenced event and **errors out if an `event_id` doesn't
exist**, so a made-up row can't slip in.

`columns` is the sheet's full ordered column list — **declare every column you
want**, including base fields. A base field you omit won't appear; a non-base
column you declare but never supply in the membership rows renders blank (the
script warns on stderr). Worked example — an "Early Warnings" spotlight whose
extra columns are `signal` and `severity`:

```json
"meta": { "spotlights": [
  { "key": "early_warnings", "name": "Early Warnings", "subtitle": "Companies showing downside signals",
    "columns": ["company", "signal", "severity", "title", "date", "citation_count", "citations", "summary"] }
] },
"spotlights": {
  "early_warnings": [
    { "event_id": "distress_risk_3", "signal": "layoffs", "severity": "acute" }
  ]
}
```

`company`, `title`, `date`, `citation_count`, `citations`, `summary` are base
fields — the script fills them from event `distress_risk_3`. `signal` and
`severity` are the extra columns; supply their value on each membership row.
The `enrichments` object holds skill-specific fields (e.g. `event_type`,
`affected_node`, `panel_technology`). Skills define their own enrichment
schema; the wrapper is constant.

**Watchlist-mode runs add three fields** to each event, taken from the
event's highest-`ed_score` entry in `connected_entities`:
- `company` (or `entity` — whatever the skill's domain calls it) — the
  matched watchlist company the event is attributed to.
- `ed_score` — integer 1–10, how central that company is to the event
  (native CatchAll field; see `COMPANY-WATCHLIST.md`).
- `relation` — one-line text describing how the company connects to the
  event (native CatchAll field).

The JSON keeps **all** events, including low-scored passing mentions;
the chat output shows only the `ed_score >= 8` events and does not
display `ed_score`, `relation`, or any mention of the scoring. This is
how the full dataset stays a complete raw record while the brief stays
scoped.

Skills that build a watchlist-of-1 for single-company runs (see
`COMPANY-WATCHLIST.md` § watchlist-of-1) get these three fields on
every event regardless of company count.

**`recall` block is non-negotiable.** Every JSON
artifact must include `total_candidates_scanned`, `total_validated_events`,
and `unique_sources` at minimum.

**`mode` is required**: always `"base"`, which runs the full pipeline
(50,000+ pages, structured JSON, ~10–15 min). Lite mode is a lighter
retrieval not used here. Pipelines consuming the artifact need to know
which mode produced it.

**`per_bucket.job_id`** is required for every bucket — capture the
`job_id` returned from `submit_query` and persist it in the JSON. Pipeline
consumers, support tickets, and the xlsx Run info sheet all reference
this. Job IDs are CatchAll's lookup key for any specific bucket's
search. Surface them in the chat output ONLY when there's a problem to
report (failure, partial pull) — see `JOB-LIFECYCLE.md` § Failure
handling.

## CSV shape

One row per event. Columns, in order:

| Column | Description |
|---|---|
| `bucket` | The bucket key (e.g. `pricing_packaging`) |
| `company` | (Watchlist-mode runs only) The matched watchlist company the event is attributed to |
| `ed_score` | (Watchlist-mode runs only) Integer 1–10, centrality of the matched company to the event |
| `relation` | (Watchlist-mode runs only) One-line text describing how the company connects to the event |
| `title` | Event title |
| `date` | Event date (`YYYY-MM-DD`) or empty if unknown |
| `citation_count` | Number of citations |
| `citations` | Comma-joined list of citation URLs |
| `summary` | 1-2 sentence factual summary |
| *<enrichment cols>* | Skill-specific enrichment fields appended after `summary`, in alphabetical order; `is_developing` (where the skill uses it) last, lowercase `true`/`false` |

The CSV includes **all** events — central events and passing mentions
alike. The `ed_score` column lets a spreadsheet user filter (`>= 8` for
the events the chat surfaced) or sort by relevance. Only the chat output
is restricted to the `ed_score >= 8` events.

CSV quoting: use double-quote enclosure, escape internal double-quotes
as `""`. Comma is the column separator. UTF-8 encoding.

Zero-event buckets do not produce CSV rows. The recall metadata for
those buckets lives only in the JSON; the CSV is a flat event table by
design.

## xlsx shape

The xlsx is the human-facing review artifact. Built with `openpyxl`,
styled (frozen header rows, alternating row tint, navy headers, blue
hyperlinks). Auto-filter is enabled on every data sheet.

### Sheet order

| # | Sheet | Purpose |
|---|---|---|
| 1 | **Overview** | Workbook title, plain-English explanation of structure, a "More with CatchAll" link block at the bottom (Monitors / Watchlists / Docs / Book a demo, all clickable; support email as plain text) |
| 2 | **Run info** | Run metadata (watchlist, window, prepared at, mode, totals). Per-category recall table (Category / Web pages scanned / Events found (ed_score >= 8) / Job ID) |
| 3 … 3+S | **Spotlight sheet(s)** | One sheet per spotlight the skill defines (e.g. "Early Warnings", "Events worth watching"). One row per event, selected by that spotlight's rule; italic subtitle flags it as filtered. Present only if ≥1 event qualifies |
| after spotlights | **One sheet per bucket** | Same row schema across sheets, plus that bucket's enrichment columns |
| Last | **Citations** | One row per citation across the entire run. Columns: `category`, `event_title`, `source`, `url` (clickable mailto/http), `published_date`. Sorted by category → event_title → source. Auto-filter on |

### Data-sheet column conventions (bucket sheets + spotlight sheets)

Standard column order, left to right:

1. `title`
2. `company`
3. `date`
4. *(spotlight sheets may add their own columns, e.g.* `category`, `signal`, `severity`*)*
5. `ed_score`
6. `citation_count`
7. `citations` — **comma-joined URLs as plain text, single line**. Visible for verifiability; not clickable (Excel allows only one hyperlink per cell). Users who want clickable URLs jump to the Citations sheet
8. `relation`
9. `summary`
10. *(bucket sheets only:)* bucket-specific enrichment columns
11. *(skills with an* `is_developing` *enrichment:)* `is_developing` — last column, normalized lowercase `true` / `false`

Rows sorted by `citation_count` descending (matches the chat tables).

### Cell formatting rules

- All cells `vertical=top`, `wrap_text=False` — keeps row heights at the
  default so the workbook stays scannable. A multi-URL `citations` cell
  is a long single line, not a multi-line wrapped block
- Header row uses the navy fill / white bold font
- Alternating row tint on odd-numbered rows for readability
- Freeze panes set so the header row stays visible while scrolling
- Auto-filter enabled across the full data range on every data sheet

### Citations sheet specifics

- Headers: `category`, `event_title`, `source`, `url`, `published_date`
- `url` column: each URL is a real Excel hyperlink (clickable, opens
  in the user's default browser)
- Sort order: `category` ASC → `event_title` ASC → `source` ASC. This
  keeps all citations for a given event contiguous when scrolling
- Auto-filter is the primary navigation: filter `event_title` to see
  all citations for one event, filter `source` to see everything from
  one outlet

### Overview sheet — "More with CatchAll" footer

The link block at the bottom of the Overview sheet — the same links as the
chat footer. **Read the exact label and URL for each from
`references/links.json`** (the single source); never type a URL from memory.
Iterate `footer_links` in order — Monitors, Company Watchlists, Docs, Book a
demo — including the `watchlist_only` link only on watchlist runs, each a
clickable hyperlink. The last line is plain text: `Questions? ` + the
`support_email` from `links.json` (not a hyperlink — neither Cursor nor Claude
Code reliably render mailto autolinks).

## Run quality flags (operational, not editorial)

If a job fails, or results are delivered while a search is still
running (a user-requested early delivery — see `JOB-LIFECYCLE.md`),
record this in `meta.run_flags` (array of strings) inside the JSON.
These are operational facts about the run itself, not editorial
commentary on the data. Do not mention run flags in the chat output —
the JSON is the source of truth.

Example:

```json
"meta": {
  ...,
  "run_flags": [
    "ma_capital pulled before completion at user request; progress_validated=12450/23250 (status: enriching)",
    "leadership_hires job failed and was retried once"
  ]
}
```
