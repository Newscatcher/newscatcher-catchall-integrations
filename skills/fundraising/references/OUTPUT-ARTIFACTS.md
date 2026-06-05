# Output Artifacts Reference

Every run produces four deliverables: a markdown **chat response**, an
**xlsx** workbook, a **JSON** file, and a **CSV** file. The chat response is
for reading; the xlsx is the human-review artifact (Excel/Sheets); the JSON
is the pipeline artifact; the CSV is the lightweight tabular interchange.
This file defines the contract for the downloads and the chat layout; the
skill's `SKILL.md` defines the per-event fields (the columns).

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

- Build the **xlsx** with `openpyxl` (`pip install openpyxl --break-system-packages`
  if missing) — one focused script at the end of the run, from the in-memory
  records. This is the one allowed helper script.
- Write the **JSON** and **CSV** with the `Write` tool (hold the records in
  context; no merge script).

## The "Full dataset" block

The chat output opens with a `Full dataset:` block, immediately after the
title — three absolute paths, xlsx → JSON → CSV, two-space indent:

```
Full dataset:
  xlsx: /abs/path/ai-startups-fundraising.xlsx
  JSON: /abs/path/ai-startups-fundraising.json
  CSV:  /abs/path/ai-startups-fundraising.csv
```

- Label it **`Full dataset:`** — not "Files saved" / "Downloads".
- **Absolute paths**, resolved at run time. No "how to open" tip line.
- Elsewhere in chat, call them "the full dataset" (e.g. "12 more in the full
  dataset"), never "the download". Never embed file contents in chat.

## Top-of-output dashboard panel

Immediately after the `Full dataset:` block, a `## CatchAll findings`
dashboard table with **bolded numbers** — the recall story, the single most
important moment of the output:

```
## CatchAll findings

| Window | Prepared | Mode | Total web pages scanned | Total events found |
|---|---|---|---|---|
| May 13–20, 2026 | May 20, 2026 | Base | **24,847** | **14** |
```

`Mode` is `Base` (the full-pipeline demo default). This panel is
**non-negotiable** — it is the dashboard.

## Event table

Render the events as a markdown table (not bullets — tables show it's
structured data). **Sort rows by citation count, descending** (most-covered
first). Use the skill's own columns (defined in `SKILL.md`), always ending
with a **Sources** column = first citation domain + count, e.g.
`techcrunch.com + 4 others` (use "others", not "more"). Truncate long titles
to ~100 chars with `…`. If a chat table caps at N rows, add `(K more in the
full dataset)` below it.

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
- **`recall` block is non-negotiable** — it is the proof of comprehensive
  coverage, the most CatchAll-specific part of the artifact.
- `mode` always `"base"`; `job_id` always captured.
- The JSON keeps **all** events, raw, exactly as CatchAll returned them.
- If a job failed or hit the 90-min cap, record it in `meta.run_flags`
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

## Why this matters

A user who runs any CatchAll skill gets the same artifact shape, naming, and
recall block — one pipeline ingests them all. That consistency *is* the
product story: "structured, deduplicated, pipeline-ready."
