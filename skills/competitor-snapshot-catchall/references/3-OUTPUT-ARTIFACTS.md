# Output Artifacts Reference

Every CatchAll skill produces four deliverables: a markdown chat
response, an xlsx workbook, a JSON file, and a CSV file. The chat
response is for reading; the xlsx is the human-review artifact (open
in Excel/Sheets); the JSON is the pipeline artifact; the CSV is the
lightweight tabular interchange format. This file defines the contract
for the downloadable artifacts and the link rendering. Per-skill content
design (what fields appear, what sections are organized how) lives in
the skill's `SKILL.md`.

## Files produced

Every run produces, at minimum:

| Filename | Purpose | Audience |
|---|---|---|
| `<slug>.xlsx` | Multi-sheet styled workbook (Overview, Run info, Events worth watching where applicable, one sheet per bucket, Citations sheet with clickable URLs) | Humans opening in Excel / Google Sheets |
| `<slug>.json` | Full hierarchical dataset with metadata. Pipeline-native | Scripting / programmatic ingestion |
| `<slug>.csv` | Flattened tabular view, one row per event | Tools that don't speak JSON (BI, R, pandas, Numbers) |

Where `<slug>` is `<entity-or-topic-slug>-<skill-name>`, lowercase,
hyphenated. Examples:

- `atlassian-competitor-snapshot.xlsx` / `.json` / `.csv`
- `apple-supply-chain.xlsx` / `.json` / `.csv` *(existing demo)*
- `pharma-ma-deals.xlsx` / `.json` / `.csv`

Save all three files to the current working directory unless the user
specifies otherwise. The xlsx is generated via the `openpyxl` Python
library (run `pip install openpyxl --break-system-packages` if not
present).

## The "Full dataset" block

The chat output begins with a `Full dataset:` block, immediately after
the title — three absolute file paths in plain text, in xlsx → JSON →
CSV order (xlsx first because it's the most-used deliverable for
human readers):

```
Full dataset:
  xlsx: /Users/dariochincha/Documents/catchall-demos/atlassian-competitor-snapshot.xlsx
  JSON: /Users/dariochincha/Documents/catchall-demos/atlassian-competitor-snapshot.json
  CSV:  /Users/dariochincha/Documents/catchall-demos/atlassian-competitor-snapshot.csv
```

Notes:

- Label it **`Full dataset:`** — not "Files saved", not "Downloads".
  "Full dataset" tells the reader *what* the files are (the complete
  result set) rather than narrating a file-write.
- **No "how to open" tip line.** Don't add cmd+click / `open <path>`
  instructions — the paths are self-explanatory and the extra line is
  noise.
- Use **absolute paths** (resolved from the working directory at run
  time), not relative. JSON first, then CSV. Two-space indent.
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

Use "events found" consistently across all skills and all buckets. Per-bucket
noun variation (deals/launches/moves) was tried and reverted — it added
read overhead without enough payoff, and inconsistency between sibling
sections made multi-bucket runs harder to scan. Stick with "events."

JSON/CSV columns stay technical (`event_title`, `event_date`, `citations`)
for pipeline consistency.

## Top-of-output dashboard panel

The run-level metrics (window, prepared date, total web pages scanned,
total events found) appear in a dashboard table at the top of every
chat response, immediately after the `Full dataset:` block. This is the
single most important moment of the output — it must draw the eye, not
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

The `Mode` cell is `Base` for full-pipeline runs (the demo default) or
`Lite` for lighter retrieval. Mode is also in `meta.mode` in the JSON;
surfacing it in chat tells the user which configuration produced the
result, useful if they later go into the CatchAll UI to reproduce or
extend the search.

Per-event source attribution lives in the Sources column of each
bucket's event table — no aggregate "unique sources" count in the
dashboard. The aggregate is ambiguous (could be misread as "CatchAll
only checked N sources") and adds little over the per-event view.

Tables render visually in Claude Code, Cursor, claude.ai, and most
markdown UIs. The bold on numbers focuses attention on the recall
story. This panel is **non-negotiable across all CatchAll skills** —
it is the dashboard.

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
bullets. Tables emphasize that the output is structured data, which is
the product story. Bullets read as narrative summary.

**Row order** — sort events by **citation count, descending** (most-
covered first). Citation count is the most-covered proxy for "story
importance" and is the same axis the reader is reading in the Sources
column, so the table reads top-down from biggest story to smallest. This
sort applies to every bucket table and to any cross-cutting section
(e.g. "Events worth watching"), so the reader can compare across
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
  would have produced, which is the structured-data demo.
- **Takes space** — the section sits visually alongside non-empty
  sections rather than collapsing to a single line.
- Confirms **coverage** — `33,250 web pages scanned` is right there in
  the header, no ambiguity about whether the bucket was really searched.

Use exactly `_No events found in this window._` in the first cell.
**Leave the other cells blank — do not use em-dashes.** Em-dashes
imply "no data found for this specific field," which is wrong: the
whole row doesn't exist. Blank cells read as intentionally empty.

**Do not add commentary about what the candidate noise was.** The
`noise_description` for that bucket stays in the JSON for pipeline
consumers; in chat, the user trusts the recall number and doesn't
need a justification tour.

## No agent-written caveats

CatchAll does not return warnings or validator-confidence flags. Do
not have the agent add its own caveats, footnotes, or validator
second-guessing to the output. The skill renders the raw API result as-is.
If CatchAll's validator misattributes an event (e.g., catches the wrong
company), that fact stays in the data — the user evaluates the raw
output and forms their own judgment, as they would when calling CatchAll
directly. Editorializing about data quality undermines the demo.

(If CatchAll ever adds API-level warnings, those can be surfaced — but
only API-returned content, not agent analysis.)

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

Every JSON artifact has the same top-level structure:

```json
{
  "meta": {
    "entity": "<competitor name | topic | watchlist name>",
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
        "validated_events": 2,
        "noise_description": "<one-line characterization of candidate noise, especially when validated=0>"
      }
    }
  },
  "events": {
    "<bucket_key>": [
      {
        "title": "<event title>",
        "date": "<YYYY-MM-DD | null>",
        "summary": "<1-2 sentence factual summary>",
        "citations": [
          { "source": "<domain>", "url": "<full URL>", "published_date": "<YYYY-MM-DD | null>" }
        ],
        "enrichments": { "<custom field>": "<value>" }
      }
    ]
  }
}
```

**Required keys per event**: `title`, `date`, `summary`, `citations`.
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

Skills that build a watchlist-of-1 for single-company runs (e.g.
competitor-snapshot — see `COMPANY-WATCHLIST.md` § watchlist-of-1) get
these three fields on every event regardless of competitor count.

**`recall` block is non-negotiable.** It is the most CatchAll-specific
field in the artifact — the proof of comprehensive coverage. Every JSON
artifact must include `total_candidates_scanned`, `total_validated_events`,
and `unique_sources` at minimum.

**`mode` is required**: always `"base"` for demo-mode skills, which run
the full pipeline (50,000+ pages, structured JSON, ~10–15 min). Lite
mode is a lighter retrieval and is not what these demos showcase.
Pipelines consuming the artifact need to know which mode produced it.

**`per_bucket.noise_description`** is required when `validated_events == 0`
and `candidates_scanned > 0`. It tells the reader what the candidate
volume actually was (e.g. "13F institutional position changes, not deal
activity"). For non-empty buckets, this field can be omitted.

**`per_bucket.job_id`** is required for every bucket — capture the
`job_id` returned from `submit_query` and persist it in the JSON. Pipeline
consumers, support tickets, and the xlsx Run info sheet all reference
this. Job IDs are CatchAll's lookup key for any specific bucket's
search. Surface them in the chat output ONLY when there's a problem to
report (timeout, failure, partial pull) — see `2-JOB-LIFECYCLE.md`
§ Failure handling.

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
| `summary` | 1-2 sentence factual summary |
| `citation_count` | Number of citations |
| `sources` | Semicolon-joined list of citation source domains |
| `urls` | Semicolon-joined list of citation URLs |
| *<enrichment cols>* | Skill-specific enrichment fields appended after `urls`, in alphabetical order |

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
| 3 | **Events worth watching** | Cross-cutting view, only present if any event has `is_developing = true` AND `ed_score >= 8`. Italic subtitle flags it as filtered |
| 4 to 4+N | **One sheet per bucket** | Same row schema across sheets, plus that bucket's enrichment columns |
| Last | **Citations** | One row per citation across the entire run. Columns: `category`, `event_title`, `source`, `url` (clickable mailto/http), `published_date`. Sorted by category → event_title → source. Auto-filter on |

### Data-sheet column conventions (bucket sheets + Events worth watching)

Standard column order, left to right:

1. `title`
2. `company`
3. `date`
4. *(only on Events worth watching:)* `category`
5. `ed_score`
6. `citation_count`
7. `citations` — **comma-joined URLs as plain text, single line**. Visible for verifiability; not clickable (Excel allows only one hyperlink per cell). Users who want clickable URLs jump to the Citations sheet
8. `relation`
9. `summary`
10. *(bucket sheets only:)* bucket-specific enrichment columns
11. `is_developing` — always the last column, normalized lowercase `true` / `false`

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

Five hyperlinks at the bottom of the Overview sheet, matching the chat
output's footer (see `4-NEXT-STEPS.md`):

- Run this on a schedule with Monitors → Monitors docs
- Learn about Company Watchlists → Watchlist docs (for watchlist skills only)
- Docs — CatchAll Quickstart → Quickstart docs
- Book a demo → booking page
- `Questions? support@newscatcherapi.com` → plain text (matches chat;
  neither Cursor nor Claude Code reliably render mailto autolinks)

## Run quality flags (operational, not editorial)

If a job fails or the run hits the 90-minute cap (see
`2-JOB-LIFECYCLE.md`), record this in `meta.run_flags` (array of
strings) inside the JSON. These are operational facts about the run
itself, not editorial commentary on the data. Do not mention run
flags in the chat output — the JSON is the source of truth.

Example:

```json
"meta": {
  ...,
  "run_flags": [
    "ma_capital search did not finish before the 90-minute cap; pulled at progress_validated=12450/23250 (status: enriching)",
    "leadership_hires job failed and was retried once"
  ]
}
```

## What standardization buys you

A user who runs three different CatchAll skills (competitor snapshot,
M&A deals, supply chain watchlist) gets three artifact pairs with the
same shape, the same naming convention, the same recall block, and the
same link rendering. They can write one pipeline that ingests any of
them. That consistency is part of the product story: "structured,
deduplicated, pipeline-ready" only holds if every skill outputs the
same shape.
