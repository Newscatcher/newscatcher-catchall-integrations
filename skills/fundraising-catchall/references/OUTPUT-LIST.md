# Output List Reference

Every run ends with a markdown **chat response** and three downloads — an
**xlsx** workbook, a **JSON** file, and a **CSV** file — delivered together as
one clean block (built up-front for normal-size results, offered for large
ones; see § Downloads). The chat response is for reading; the xlsx is the
human-review artifact (Excel/Sheets); the JSON is the pipeline artifact; the
CSV is the lightweight tabular interchange. This file defines the contract for
those downloads and the chat layout; the skill's `SKILL.md` defines the
per-event fields (the columns).

This is a **single-query** skill: one CatchAll job → one flat list of
events. No buckets, no watchlist.

## Files produced

| Filename | Purpose | Audience |
|---|---|---|
| `<slug>.xlsx` | Styled workbook: Overview, Run info, Events, Citations | Humans in Excel / Google Sheets |
| `<slug>.json` | Full hierarchical dataset with metadata | Scripting / pipelines |
| `<slug>.csv` | Flattened table, one row per event | BI / pandas / Numbers |

`<slug>` = `<topic-slug>-<skill-name>`, lowercase, hyphenated — e.g.
`ai-startups-fundraising`, `fintech-mergers-and-acquisitions`. Save all three
to the current working directory unless the user says otherwise.

All three downloads are built by the bundled **`scripts/build_downloads.py`**
(never hand-written with the `Write` tool). See **§ Downloads** for when (auto
vs offer).

## Downloads — build first, then deliver one clean block

The deliverable is **one uninterrupted block** — `## CatchAll findings` panel →
event table → `Saved:` paths → footer — with **no tool activity between its
parts.** Under MCP-only that means: **do the whole build first, silently, then
write the block in one pass.** The records hand-off and the script run sit
*above* the block as setup; they never land between the table and the `Saved:`
paths, where they'd drown the links and the footer. By size:

- **≤ ~100 records — build all three first, silently**, then render the full
  block at once. The files already exist when the table appears, so the
  `Saved:` paths sit directly under the table — **no "coming in a moment" line,
  no gap.**
- **> ~100 records — don't build** (a large build drags). Render panel → table
  → one-line offer → footer (no `Saved:` block); build on request:
  > Want the full dataset as a spreadsheet, CSV, or JSON? Just let me know.

The chat table lands a few seconds later this way (after the build) instead of
before it — negligible against a multi-minute search, and it keeps the panel,
table, links, and footer **together** instead of split by build noise. (~100 =
tunable cap.)

**Build with the bundled `scripts/build_downloads.py` — never write a build
script.** It does **no network call and uses no API key**: you pull the records
through the **MCP** (`pull_results`); the script only formats them (columns are
data-driven from the enrichment fields). Because the script is bundled, the
build is just a file write + a run — fast enough to finish before the table.

1. Save the `pull_results` output to `records.json` **as compact, single-line
   JSON** (no indentation — `json.dumps(obj)` with no `indent`). This keeps the
   hand-off **one line** in the transcript, not hundreds. (If the host already
   saved the MCP response to disk, point `--input` at that — no re-write needed.)
2. Run: `python3 scripts/build_downloads.py --input records.json --slug <slug>
   --skill <name> --topic "<topic>" --start <YYYY-MM-DD> --end <YYYY-MM-DD>`
3. Read its stdout for the file paths, then render the block with the `Saved:`
   paths already in place.

It installs `openpyxl` if missing and skips only a format it truly can't build
(CSV/JSON always work) — no raw error, no narration.

**Surface the built files per environment:**
- **Local working-dir** (Claude Code / Cursor): a `Saved:` block — absolute
  paths, xlsx → JSON → CSV, two-space indent:
  ```
  Saved:
    xlsx: /abs/path/<slug>.xlsx
    JSON: /abs/path/<slug>.json
    CSV:  /abs/path/<slug>.csv
  ```
- **claude.ai**: the download buttons it appends are the delivery — don't print
  the `/mnt/...` paths.

Never embed file contents in chat.

## Top-of-output dashboard panel

The chat **opens** with a `## CatchAll findings` dashboard table with
**bolded numbers**:

```
## CatchAll findings

| Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|
| May 13–20, 2026 | May 20, 2026 | Base | **24,847** | **14** |
```

`Mode` is `Base` (the full-pipeline default). This panel is
**non-negotiable**.

## Event table

Render the events as a markdown table (not bullets — tables show it's
structured data). **Sort rows by citation count, descending** (most-covered
first). Use the skill's own columns (defined in `SKILL.md`), always ending
with a **Sources** column = first citation domain + count, e.g.
`techcrunch.com + 4 others` (use "others", not "more"). Truncate long titles
to ~100 chars with `…`. If a chat table caps at N rows, add `(K more — ask and
I'll export the full set)` below it.

## Vocabulary & dates (chat)

- "web pages scanned" (not candidates), "events found" (not valid_records),
  "sources" (not citations).
- Window header `May 13–20, 2026` (en-dash, with year). Table-cell dates:
  short `May 16` joined by a non-breaking space (U+00A0) so they don't wrap.
  Never ISO (`2026-05-13`) in chat.
- JSON/CSV keep ISO dates (`YYYY-MM-DD`) and technical column names.

## Zero-event pattern

If the run returns 0 events, do **not** drop the table — it's a positive
result (nothing qualifying happened, and the web-pages-scanned count backs
it). Render the dashboard panel + the table header + one row:

```
| Event | … | Sources |
|---|---|---|
| _No events found in this window._ |  |  |
```

Use exactly `_No events found in this window._` in the first cell; leave the
rest blank (no em-dashes). No commentary about the candidate noise.

## JSON shape

```json
{
  "meta": {
    "topic": "<query topic, e.g. 'AI startup funding'>",
    "window": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" },
    "prepared_at": "<ISO 8601 UTC>",
    "skill": "<skill name>",
    "mode": "base",
    "job_id": "<UUID from submit_query>",
    "recall": {
      "total_candidates_scanned": 24847,
      "total_validated_events": 14,
      "unique_sources": 247
    }
  },
  "events": [
    {
      "title": "<event title>",
      "date": "<YYYY-MM-DD | null>",
      "summary": "<1-2 sentence factual summary>",
      "citations": [
        { "source": "<domain>", "url": "<full URL>", "published_date": "<YYYY-MM-DD | null>" }
      ],
      "enrichments": { "<skill field>": "<value>" }
    }
  ]
}
```

- Required per event: `title`, `date`, `summary`, `citations`. `enrichments`
  holds the skill's fields (the table columns).
- **`recall` block is non-negotiable**.
- `mode` always `"base"`; `job_id` always captured.
- The JSON keeps **all** events, raw, exactly as CatchAll returned them.
- If a job failed, or results were delivered while the search was still
  running (a user-requested early delivery), record it in `meta.run_flags`
  (array of strings) — operational facts only, never surfaced in chat.

## CSV shape

One row per event. Columns, in order: `title`, `date`, `summary`,
`citation_count`, `sources` (semicolon-joined domains), `urls`
(semicolon-joined URLs), then the skill's enrichment columns (alphabetical).
Double-quote enclosure, `""` to escape internal quotes, comma separator,
UTF-8.

## xlsx shape

Built with `openpyxl`, styled (navy header fill + white bold font, frozen
header row, alternating row tint, auto-filter on data sheets, blue clickable
hyperlinks). Four sheets:

| # | Sheet | Contents |
|---|---|---|
| 1 | **Overview** | Workbook title, one-line explanation of the structure, and a "More with CatchAll" link block at the bottom (Monitors / Docs / Book a demo clickable; support email plain text — see `NEXT-STEPS.md`) |
| 2 | **Run info** | topic, window, prepared_at, mode, totals (web pages scanned, events found, unique sources), job_id |
| 3 | **Events** | One row per event: `title`, `date`, `citation_count`, `citations` (comma-joined URLs, plain text), `summary`, then the skill's enrichment columns. Sorted by citation_count desc |
| 4 | **Citations** | One row per citation: `event_title`, `source`, `url` (real clickable hyperlink), `published_date`. Sorted by event_title → source. Auto-filter on |

Cells `vertical=top`, `wrap_text=False`. Header row navy/white-bold. Freeze
the header row. Auto-filter across the full data range on every data sheet.

## Footer

End the chat with the **More with CatchAll** footer — see `NEXT-STEPS.md`.
