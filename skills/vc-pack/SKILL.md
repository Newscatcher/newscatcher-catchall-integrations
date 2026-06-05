---
name: vc-pack
description: Invoke for any query about a market's funding AND acquisition
 activity together — capital flowing into and out of a sector in one view.
 Triggers on "VC pack for fintech", "funding and M&A in cybersecurity last
 30 days", "capital activity in healthcare AI", "deal activity in defense
 tech", "weekly brief on AI infra", "where is money moving in climate", or
 any request that combines both signals. Works for any market, geography,
 and timeframe up to 30 days. Use even if the user doesn't say "VC pack."
 Do NOT use for single-signal queries — if the user asks only about funding
 rounds or only about acquisitions, defer to the standalone fundraising or
 mergers-and-acquisitions skill.
---

The VC pack tracks where capital flows into a market (funding rounds) and
out of it (acquisitions). Output is a single dashboard combining both
feeds. Data comes from two parallel CatchAll jobs joined at the
presentation layer.

This skill is self-contained. Query construction, validators, and
enrichments for both feeds are in `references/EXTRACTION.md`. The
dashboard template and the render script are in `assets/`.

---

## CRITICAL: One dashboard, two feeds, no preview

The VC pack always submits two jobs and renders one dashboard.

- Never substitute one feed for the other.
- Never render partial output. The dashboard's aggregates (deal stage %,
  sub-sectors, capital ratio, top-3, mega-rounds %) are invalid until
  both feeds report `status: completed`.
- Never preview the dashboard with placeholder values while jobs are
  still running.

If only one feed completes, do not render the half-dashboard. Tell the
user which feed failed and offer to retry that side.

---

## How to interpret a request

Required dimensions:
1. **Market** — industry, vertical, or product category (cybersecurity, AI agents, fintech).
2. **Location** — city, region, country, or "global." Defaults to global if unspecified.
3. **Timeframe** — explicit window, max 30 days. Never open-ended.

If any are missing, ask before submitting.

| User input | Resolved request |
|---|---|
| "VC pack for AI agents last 7 days" | market=AI agents, location=global, timeframe=7d |
| "Funding and M&A in fintech US last 2 weeks" | market=fintech, location=United States, timeframe=14d |
| "Capital activity in cybersecurity this month" | market=cybersecurity, location=global, timeframe=30d |

**Timeframe ceiling:** 30 days per query. Wider windows must be split
into separate runs and reconciled by the user.

---

## Submit two jobs in parallel

Submit both jobs in the same turn. Order doesn't matter; wall-clock time
is shared across the two.

Before constructing queries, read `references/EXTRACTION.md` for the
forbidden-phrase rules, query formulas, validators, and enrichments. Both
feeds must use their full validator + enrichment schemas as specified.

**Funding query** — formula in EXTRACTION.md ("Funding job"). Required
enrichments: `industry_vertical` (Sub-sectors), `funding_stage_normalized`
(Deal stage), `funding_amount_value`, `funding_amount_currency`,
`investors`, `product_description`, `announcement_date`.

**M&A query** — formula in EXTRACTION.md ("M&A job"). Required enrichments:
`acquirer_type` (Acquirer type), `target_industry`, `deal_value_value`,
`deal_value_currency`, `deal_value_display`, `deal_type_display`,
`announcement_date`.

**Limit:** `limit: 50` on each job unless the user explicitly asks for an
exhaustive run. 50 is enough for a 30-day market view and bounds runtime.

After both submits return, output one sentence:

```
I'll pull together a VC pack for <market> over the last <N> days —
checking on both searches now; I'll render the dashboard once they're
done.
```

---

## Run both jobs to completion

Poll BOTH feeds to completion — do NOT hand off after a single check. The
per-job rules are the same as every CatchAll skill (`references/JOB-LIFECYCLE.md`):
sleep-safe pacing, stop only at a terminal status, a ~90-min cap. Do NOT
burn the tool-call budget on chained `sleep` calls upfront.

1. **Poll both feeds** with `get_job_status` (one call per feed) every
   ~60–90s. Pace each wait with a SINGLE background timer
   (`run_in_background`) — never a foreground `sleep`, never overlapping
   timers. A feed is done at `completed` or `failed`; `submitted` /
   `analyzing` / `fetching` / `clustering` / `enriching` all mean still
   running.
2. **Both feeds `completed`** → render the full dashboard (see "Hand the
   data to render.py" + "Render channels"). This is the normal path.
3. **Either feed `failed`** → tell the user which side failed and stop.
4. **If funding is done but M&A is still running** — after a reasonable
   wait (~20–30 min, the normal completion window) or at the 90-min cap —
   render the **funding side now** instead of making the user wait. Call
   `render.py` with
   `--funding-job-id <id>` plus `--ma-pending` (it renders funding fully and
   marks the M&A + capital cards "still searching"). Keep both `job_id`s and
   tell the user: *"Funding's ready — M&A is still searching; reply 'refresh'
   and I'll complete the dashboard."*
5. **On user follow-up** ("refresh" / "any update?") → re-check the pending
   feed. If now `completed`, re-render the full dashboard from both job IDs.
   If still running, do one more capped wait.

(If funding is the slow one, the same applies in reverse — but funding is
usually the faster feed.)

---

## CRITICAL: Hand the data to render.py — do NOT re-emit it via tokens

Once both jobs report `completed`, your job is to invoke `render.py`
with the two **job IDs**, not to pull the data and re-write it as JSON.
Re-emitting tens of thousands of records as JSON via the LLM is exactly
the bottleneck this design avoids.

There are three input modes, in priority order. Use the first one that
works in your environment.

### Mode 1 — Direct API pull (PREFERRED)

If `CATCHALL_API_KEY` is set in the environment (or you can pass
`--api-key`), render.py pulls the data over HTTP itself. You emit only
the two job IDs and the meta — sub-second, no tokens spent on data:

```bash
python /path/to/skill/assets/render.py \
  --funding-job-id <funding_job_id> \
  --ma-job-id <ma_job_id> \
  --market "Cybersecurity" \
  --location "United States" \
  --window-days 30 \
  --output /tmp/vc-pack-dashboard.html
```

Use this whenever it's available. The agent does NOT need to call
`pull_results` at all — render.py does the pulling.

### Mode 2 — Saved pull files

If your environment automatically saves large MCP responses to disk
(some Claude environments do this for tool outputs above a token limit),
pass the saved file paths directly. render.py auto-unwraps the standard
MCP `{"result": "<inner JSON>"}` envelope:

```bash
python /path/to/skill/assets/render.py \
  --funding-pull /path/to/funding-pull-result.txt \
  --ma-pull /path/to/ma-pull-result.txt \
  --market "Cybersecurity" --location "United States" \
  --window-days 30 \
  --output /tmp/vc-pack-dashboard.html
```

Use this when Mode 1 isn't available but the pull tool's output landed
on disk via the harness's auto-save behavior.

### Mode 3 — Combined input.json (LAST RESORT)

Only use this when neither Mode 1 nor Mode 2 works (Claude.ai today is
the canonical case: MCP credentials don't reach the code-execution
sandbox, and the harness doesn't auto-save MCP results to disk). This
mode requires writing the records to a file via Claude's file-write
tool, which re-emits everything through token generation. The bytes
Claude has to type ARE the wait time, so write the **minimal** shape:

```bash
python /path/to/skill/assets/render.py \
  /tmp/vc-pack-input.json \
  --output /tmp/vc-pack-dashboard.html
```

#### Minimal Mode-3 schema — write ONLY these fields

render.py reads a fixed, small set of fields. Drop everything else. In
particular: no `record_id`, no `enrichment_confidence`, no `_domain`
fields, no `_location` fields, and **citations stripped to one entry
with the link only**. That cuts the JSON Claude has to emit by roughly
50%.

Top-level shape:

```json
{
  "funding_pull": {
    "candidate_records": <int>,
    "valid_records": <int>,
    "all_records": [ <funding records — schema below> ]
  },
  "ma_pull": {
    "candidate_records": <int>,
    "valid_records": <int>,
    "all_records": [ <M&A records — schema below> ]
  },
  "meta": {
    "market": "Fintech",
    "location": "United States",
    "window_days": 14,
    "start_date": "2026-04-19",
    "end_date":   "2026-05-03"
  }
}
```

Funding record (each entry in `funding_pull.all_records`):

```json
{
  "record_title": "<fallback title, only if company_name missing>",
  "enrichment": {
    "company_name":              "MagicCube",
    "product_description":       "<one-sentence description>",
    "industry_vertical":         "payments",
    "funding_round":             "Series A",
    "funding_stage_normalized":  "series_a",
    "funding_amount_value":      10000000,
    "funding_amount_currency":   "USD",
    "funding_amount_display":    "$10M",
    "announcement_date":         "2026-04-28",
    "investors":                 "e& capital, Verifone, Bold Capital"
  },
  "citations": [{ "link": "https://example.com/article" }]
}
```

M&A record (each entry in `ma_pull.all_records`):

```json
{
  "record_title": "<fallback title, only if target_name missing>",
  "enrichment": {
    "target_name":         "Capital One IRA deposits",
    "target_industry":     "wealthtech",
    "deal_type_display":   "Asset Purchase",
    "acquirer_name":       "Axos Bank",
    "acquirer_type":       "strategic",
    "deal_value_value":    3200000000,
    "deal_value_currency": "USD",
    "deal_value_display":  "$3.2B",
    "announcement_date":   "2026-04-22"
  },
  "citations": [{ "link": "https://example.com/article" }]
}
```

That is the EXHAUSTIVE list of fields render.py reads. Anything else in
the raw CatchAll response is dead weight in Mode 3 — strip it. Citations
beyond `citations[0].link` are not used; cut them.

Do not pretty-print the JSON. Compact form (no indentation, single line
per record) is fine and shorter to type.

### What render.py does after that

Regardless of mode, render.py does all aggregation (FX conversion via
`urllib` to open.er-api.com, deal stage buckets, sub-sectors, capital
ratio, top-3 lists, mega rounds, row pre-rendering, minification). You
do not compute aggregates in chat tokens.

---

## Dataset downloads (xlsx / JSON / CSV)

The dashboard is the visual; the downloadable dataset is the structured
proof, and it makes vc-pack match the other CatchAll skills. On the render.py
call, also pass **`--data-out <prefix>`** — it writes `<prefix>.json`,
`.csv`, and `.xlsx` (the funding + M&A records) alongside the HTML, with no
change to the dashboard. Use `<prefix>` = `<cwd>/<market-slug>-vc-pack`
(e.g. `/abs/cwd/fintech-vc-pack`). Install openpyxl first if the xlsx is
wanted: `pip install openpyxl --break-system-packages` (without it, render.py
still writes the JSON + CSV and notes the skip).

Then include a `Full dataset:` block — absolute paths, xlsx → JSON → CSV,
two-space indent — **below the dashboard banner** (the dashboard is the lead;
the downloads support it):

```
Full dataset:
  xlsx: /abs/cwd/fintech-vc-pack.xlsx
  JSON: /abs/cwd/fintech-vc-pack.json
  CSV:  /abs/cwd/fintech-vc-pack.csv
```

Label it `Full dataset:` (not "Downloads"). When the M&A feed is still
pending (`--ma-pending`), the files contain the funding records plus an
empty M&A set and `meta.ma_pending: true` — refresh regenerates them.

---

## Render channels

The dashboard is the deliverable in every environment. Pick the best
channel available and fall through if a tier fails.

All examples below use Mode 1 (direct-pull). Substitute Mode 2 / Mode 3
flags if Mode 1 isn't available.

### Pre-flight — render to file first, then pick a tier by size

`show_widget` has an undocumented size ceiling — large dashboards
(roughly >50 KB minified, which corresponds to ~30-day windows with 40+
total deals) reliably time out. Trying it anyway and falling back wastes
30–90 s on the timeout. Avoid that by always rendering to a file first
and using the file size to pick the tier:

```bash
OUT=/tmp/vc-pack-dashboard.html
DATA="$PWD/cybersecurity-vc-pack"   # <market-slug>-vc-pack in the working dir
python /path/to/skill/assets/render.py \
  --funding-job-id <funding_job_id> \
  --ma-job-id <ma_job_id> \
  --market "Cybersecurity" --location "United States" --window-days 30 \
  --data-out "$DATA" \
  --output "$OUT"
SIZE=$(wc -c < "$OUT")
```

Then:

- If `visualize:show_widget` is available **AND** `$SIZE < 50000` → Tier 1
- Else if filesystem write to a user-visible location is available → Tier 2
- Else → Tier 3 (re-render with `--format markdown`)

This pattern costs one extra `wc -c` but eliminates the show_widget
timeout penalty entirely on large windows.

### Tier 1 — inline widget (Claude.ai, smaller HTML only)

**Detect:** `visualize:show_widget` tool is available **and** rendered
HTML is under 50 KB (per the pre-flight check above).

**Render:** read the already-written file and pass to `show_widget`:

```bash
# $OUT is already populated from the pre-flight render
HTML=$(cat "$OUT")
```

Then pass `$HTML` to `show_widget` as `widget_code`.

If `show_widget` still returns "No result received" or times out anyway,
retry once more (2 attempts total). The file is on disk — retry is one
more tool call. After 2 failures, **fall through to Tier 2**, do not
error. Do not retry beyond 2 attempts; the size check made any further
retry unlikely to succeed.

### Tier 2 — file delivery (large dashboards or no widget tool)

**Detect:** Tier 1 unavailable OR the rendered HTML is too big for the
inline widget (the pre-flight check decided this).

**Render:** the file is already on disk from the pre-flight render. Move
it to a user-visible location and either auto-open it (Claude Code,
Cursor, IDEs) or use whatever file-presentation tool the host exposes
(`present_files`, etc.):

```bash
# On Claude Code / Cursor / desktop IDEs — auto-open in browser:
DIR="$HOME/.cache/vc-pack"          # %LOCALAPPDATA%\vc-pack on Windows
mkdir -p "$DIR"
TS=$(date +%Y%m%d-%H%M%S)
DEST="$DIR/dashboard-$TS.html"
mv "$OUT" "$DEST"
open "$DEST" 2>/dev/null || xdg-open "$DEST" 2>/dev/null || start "$DEST" 2>/dev/null
echo "$DEST"

# On Claude.ai (no shell `open`) — move to outputs and let the host present it:
mkdir -p /mnt/user-data/outputs
DEST=/mnt/user-data/outputs/vc-pack-dashboard-$(date +%Y%m%d-%H%M%S).html
mv "$OUT" "$DEST"
# Then call present_files (or whatever file-presentation tool is exposed)
# with the path "$DEST".
```

Print to chat — a clean two-line header (no figlet), then the dashboard's
**clickable blue link flanked by arrows** pointing in at it, so it's
obviously the thing to click. The link is a real markdown `file://` link so
it renders blue and cmd/ctrl+click-able (same mechanism as the footer links):

**VC PACK** — <Market>
funding + M&A · last <N> days

The dashboard just opened in your browser — reopen it anytime:
▶▶▶ **[Open the dashboard](file://<ABSOLUTE path to the .html>)** ◀◀◀

- The open link **must be a markdown link with a `file://` URL + the absolute
  path** — note the three slashes (`file://` + the path's leading `/`), e.g.
  `file:///Users/you/.cache/vc-pack/dashboard-20260605-002841.html`.
  cmd/ctrl+click opens it in the browser. (The dashboard also already
  auto-opened via the `open`/`xdg-open` step above — this is the re-open link.)
- Keep the `▶▶▶ … ◀◀◀` arrows tight around the link so it reads as the target.
  Link text is just **Open the dashboard** — no `↗` or other trailing glyph.
- The `Full dataset:` block and the footer follow below.

The HTML is self-contained (inline CSS + JS, no `fetch()`), so `file://`
works fine. No server lifecycle, no port collisions.

### Tier 3 — markdown (text-only environments)

**Detect:** Tier 1 and 2 both unavailable.

**Render:** re-run render.py with `--format markdown` (or, if the HTML
file from the pre-flight render is still around, just discard it):

```bash
python /path/to/skill/assets/render.py \
  --funding-job-id <funding_job_id> \
  --ma-job-id <ma_job_id> \
  --market "Cybersecurity" --location "United States" --window-days 30 \
  --format markdown
```

Emits KPI lines, funding + M&A tables, and a one-line capital flow
summary. Same data, no charts. This is a fallback so the skill doesn't
dead-end — not a feature.

### Channel selection in code

```
1. If `visualize:show_widget` exists                       → Tier 1
2. Else if bash + filesystem write to user's home          → Tier 2
3. Else                                                    → Tier 3

If a tier fails at runtime, drop to the next tier. The user wants the
dashboard, not a status report on render plumbing.
```

---

## Output rules

- The dashboard is the output. One sentence preamble (or none), render,
  stop.
- **Never web-search, `WebFetch`, verify, dedupe, or re-judge the records.**
  The dashboard renders CatchAll's raw output as-is — this is a demo of the
  product, not an analysis of it. If a record looks off, that's CatchAll's
  product domain, not something to audit here.
- Do not narrate polling, FX fetching, or render mechanics. The
  dashboard's run-stats strip and FX footer surface what users need to
  know about provenance.
- Do not comment on match rate, candidate volume, runtime, validator
  strictness, or query tightness. Wide pool with small `dealsFound`
  count is normal CatchAll behavior.
- Do not suggest narrower queries unless the user asks.
- Flag in chat only on real failures: feed status `failed`, zero deals
  found in either feed, or unresolved FX after a `retry`.
- No Word doc, PDF, or spreadsheet alongside the dashboard unless the
  user asks.
- End the chat output (after the dashboard) with the **More with CatchAll**
  footer from `references/NEXT-STEPS.md`, rendered verbatim as the last line.

### "retry" resume after FX failure

If render.py emits the dashboard in USD-only mode (FX endpoint failed
with mixed-currency data), the footer says:

> FX unavailable — N non-USD deals excluded from totals. Reply 'retry'
> to retry conversion.

When the user replies "retry," re-run render.py only (no need to
re-pull CatchAll). It re-attempts the FX fetch and re-aggregates.
Sub-30s round trip.
