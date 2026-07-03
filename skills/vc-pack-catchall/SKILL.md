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

Query construction, validators, and
enrichments for both feeds are defined in § Building the two queries. The
render script is in `scripts/`; the dashboard template it fills is in
`assets/`.

---

## CRITICAL: One dashboard, two feeds — the partial is a progress line, not the dashboard

The VC pack always submits two jobs and renders one dashboard.

- Never substitute one feed for the other.
- **The DASHBOARD never renders partial.** Its aggregates (deal stage %,
  sub-sectors, capital ratio, top-3, mega-rounds %) are invalid until both
  feeds report `status: completed` — never preview it with placeholder values.
- **Progress shows as the live table** in `references/CONCURRENCY.md` (both
  feeds, with status + counts, updated as the run goes) — never the dashboard,
  and never one feed's results dressed up as the whole. The full dashboard
  renders only when both feeds complete.

If a feed `failed` (not merely slow), tell the user which side failed and offer
to retry it.

---

## How to interpret a request

Required dimensions:
1. **Market** — industry, vertical, or product category (cybersecurity, AI agents, fintech).
2. **Location** — city, region, country, or "global." Defaults to global if unspecified.
3. **Timeframe** — explicit window, max 30 days. Never open-ended.

If any are missing, ask before submitting (use the standard time-window
question in `references/QUERY-REVIEW.md`, combined with the `Max results`
picker in one step).

| User input | Resolved request |
|---|---|
| "VC pack for AI agents last 7 days" | market=AI agents, location=global, timeframe=7d |
| "Funding and M&A in fintech US last 2 weeks" | market=fintech, location=United States, timeframe=14d |
| "Capital activity in cybersecurity this month" | market=cybersecurity, location=global, timeframe=30d |

**Timeframe ceiling:** 30 days per query. Wider windows must be split
into separate runs and reconciled by the user.

---

## Building the two queries

### CRITICAL: Never query for web pages

Before constructing any query, run this self-check:

**Does my query contain any of these forbidden phrases?**

- `news articles`, `news stories`, `articles about`, `stories about`
- `press coverage`, `media coverage`, `NLP summary`
- `recent news`, `news on`, `coverage of`, `reports on`
- `find articles`, `search articles`, `get articles`

If yes -- **stop and rewrite**. The query must describe what happened in
the world, not what was written about it.

**Wrong:** `"news articles about Series B raises in Austin last 30 days"`
**Right:** `"Series B funding rounds announced in Austin in the last 30 days"`

**Wrong:** `"find articles covering AI company acquisitions last month"`
**Right:** `"AI companies that announced an acquisition in the last 30 days"`

Validators and enrichments must also be event-scoped. Never write
`"web page mentions a funding round"` -- write `"a company has officially
announced a closed funding round"`.

### Constraint cap (applies to both feeds)

Cap each query at 4 meaningful constraints. More than that and results
will silently return nothing -- CatchAll can't match a 6-way
intersection that rarely appears in a single source.

Safe to include (commonly disclosed in announcements):
- Event type (round stage, deal type)
- Industry / market
- Location
- Timeframe
- Amount threshold ("over $10M", "under $1B")

Avoid (rarely in source articles):
- Investor tier / fund size
- Founder demographics
- Acquirer AUM
- Founding year
- Headcount

### Funding job

#### Query formula

`"<event verb> + <stage if specified> + <industry/market> + <location> + <timeframe>"`

Use natural language. CatchAll interprets it -- don't reduce to keywords.

| User intent | Query |
|---|---|
| AI agents funding last 7 days | `"funding rounds announced by AI agent startups in the last 7 days"` |
| Cybersecurity US last 30 days | `"funding rounds announced by cybersecurity companies in the United States in the last 30 days"` |
| Series B fintech Europe | `"Series B funding rounds announced by fintech companies in Europe in the last 30 days"` |

#### Query signal terms (include at least one)

`raised, secures funding, closes round, announces investment, seed round,
Series A, Series B, funding announcement, backed by, led by`

#### Valid funding events

- Officially announced closed/completed round
- Confirmed by the company, named investor, or credible source
- Amount or stage publicly disclosed

#### Excluded

Rumors, funding targets, government grants, IPOs, SPACs, debt financing.

#### Validators

```json
[
  {
    "name": "is_funding_announcement",
    "description": "True only if the event reports a company that has officially announced a closed or completed funding round, confirmed by the company, a named investor, or a credible source. False for rumors, funding targets, grants, IPOs, or debt financing.",
    "type": "boolean"
  },
  {
    "name": "location_match",
    "description": "True if the company is headquartered in or primarily operating from the specified geographic area. If no location was specified, set to true for all results.",
    "type": "boolean"
  },
  {
    "name": "event_in_timeframe",
    "description": "True if the funding announcement was made or confirmed within the requested time window. False if the date is unconfirmed or outside the window.",
    "type": "boolean"
  },
  {
    "name": "stage_match",
    "description": "True if the funding round matches the requested stage or stage range. If no stage was specified, set to true for all results.",
    "type": "boolean"
  }
]
```

#### Enrichments

Required for the VC pack dashboard:

```json
[
  { "name": "company_name", "description": "Name of the company that raised funding", "type": "text" },
  { "name": "company_domain", "description": "Company website domain if available", "type": "text" },

  { "name": "funding_round", "description": "Original stage label as reported (e.g. Series B2, Seed Extension)", "type": "text" },
  { "name": "funding_stage_normalized", "description": "Normalized stage: pre-seed, seed, series_a, series_b, series_c, growth, unknown", "type": "text" },

  { "name": "funding_amount_value", "description": "Numeric value of funding amount only (e.g. 5000000)", "type": "number" },
  { "name": "funding_amount_currency", "description": "Currency of funding amount (USD, EUR, GBP, etc.)", "type": "text" },
  { "name": "funding_amount_display", "description": "Formatted funding amount for display (e.g. $5M, €3.2M, Undisclosed)", "type": "text" },

  { "name": "announcement_date", "description": "Date the funding round was officially announced or confirmed", "type": "date" },

  { "name": "product_description", "description": "One-sentence description of what the company does or makes, extracted from the funding announcement. Focus on the core product or service, not the funding round itself. Example: 'AI-powered code editor for software developers' or 'B2B fintech platform for SMB lending'.", "type": "text" },

  { "name": "investors", "description": "Named lead investors or participating firms, if disclosed. Return as a list or comma-separated string.", "type": "text" },
  { "name": "company_location", "description": "City, region, or country where the company is headquartered", "type": "text" },
  { "name": "industry_vertical", "description": "Specific industry sub-vertical of the company (e.g. 'identity', 'fraud', 'threat-intel', 'fintech', 'AI infrastructure', 'humanoid robots'), not an umbrella term ('cybersecurity', 'robotics'). One short lowercase phrase, plural preferred. No comma-joined lists.", "type": "text" }
]
```

`industry_vertical` powers the **Sub-sectors by deal count** card. Prefer
specific labels (e.g. "identity", "SOC/SecOps") over umbrella terms
(e.g. "cybersecurity") because the sub-sector card aggregates within a
market, not across markets.

`funding_stage_normalized` powers the **Deal stage** card. Must use the
exact enum values listed.

`investors` powers the **Most active investors** card and the table's
"Select investors" column.

#### Source URL

Use `citations[0].link` from the underlying record. Not in the
enrichment schema -- the citations list is populated by clustering, not
LLM extraction.

### M&A job

#### Query formula

`"<target description> + <event verb> + <location> + <timeframe>"`

| User intent | Query |
|---|---|
| AI agents M&A last 7 days | `"AI agent companies that were acquired in the last 7 days"` |
| Cybersecurity US last 30 days | `"cybersecurity companies that were acquired or merged in the United States in the last 30 days"` |
| Healthcare AI Europe | `"healthcare AI companies that announced an acquisition in Europe in the last 30 days"` |

#### Query signal terms (include at least one)

`acquires, acquired by, merges with, merger, takeover, asset purchase,
buys, deal closed, acquisition announced, acqui-hire, combines with`

#### Valid M&A events

- Officially announced acquisition, merger, asset purchase, or acqui-hire
- Confirmed ownership transfer or merger announcement

#### Excluded

Rumors, partnerships without ownership transfer, funding rounds, IPOs,
licensing deals, minority stakes.

#### Validators

```json
[
  {
    "name": "is_ma_event",
    "description": "True only if the event reports a confirmed merger, acquisition, asset purchase, or acqui-hire. False for rumors, partnerships, funding rounds, IPOs, or licensing deals.",
    "type": "boolean"
  },
  {
    "name": "location_match",
    "description": "True if either the acquirer or target is headquartered in or primarily operating from the specified geographic area. If no location was specified, set to true for all results.",
    "type": "boolean"
  },
  {
    "name": "event_in_timeframe",
    "description": "True if the deal announcement was made or confirmed within the requested time window. False if the date is unconfirmed or outside the window.",
    "type": "boolean"
  },
  {
    "name": "industry_match",
    "description": "True if the target's industry/vertical matches the requested market. If no market was specified, set to true for all results.",
    "type": "boolean"
  }
]
```

#### Enrichments

Required for the VC pack dashboard:

```json
[
  { "name": "acquirer_name", "description": "Name of the company making the acquisition or initiating the merger", "type": "text" },
  { "name": "acquirer_domain", "description": "Acquirer website domain if available", "type": "text" },
  { "name": "acquirer_location", "description": "City, region, or country where the acquirer is headquartered", "type": "text" },

  { "name": "acquirer_type", "description": "Categorize the acquirer using the standard M&A taxonomy. Output value MUST be exactly one of these four literal strings, with no additional text, qualifiers, or parentheticals: 'big_tech', 'strategic', 'financial', or 'other'. Definitions: 'big_tech' = one of Amazon, Microsoft, Google/Alphabet, Apple, Meta, NVIDIA, Anthropic, OpenAI, or a subsidiary thereof (DeepMind, AWS, etc.); 'strategic' = any other operating company acquirer (regardless of size, vertical adjacency, or public/private status); 'financial' = PE firm, holding company, family office, search fund, or other financial sponsor; 'other' = ambiguous, unknown, or doesn't fit the above (e.g. government, non-profit, individual). Pick the single best fit and return only the bare label.", "type": "text" },

  { "name": "target_name", "description": "Name of the company being acquired or merging", "type": "text" },
  { "name": "target_domain", "description": "Target company website domain if available", "type": "text" },
  { "name": "target_location", "description": "City, region, or country where the target is headquartered", "type": "text" },
  { "name": "target_industry", "description": "Specific industry sub-vertical of the target company (e.g. 'identity', 'fraud', 'fintech', 'humanoid robots'). One short lowercase phrase, plural preferred. No umbrella terms, no comma-joined lists.", "type": "text" },

  { "name": "deal_type_raw", "description": "Event type as originally reported (e.g. 'acquires', 'merges with', 'buys assets of')", "type": "text" },
  { "name": "deal_type_normalized", "description": "Normalized event type: acquisition, merger, asset_purchase, acqui_hire, unknown", "type": "text" },
  { "name": "deal_type_display", "description": "Formatted event type for UI display (e.g. Acquisition, Merger, Asset Purchase, Acqui-hire)", "type": "text" },

  { "name": "deal_value_value", "description": "Numeric value of deal amount if disclosed (e.g. 500000000)", "type": "number" },
  { "name": "deal_value_currency", "description": "Currency of deal value (USD, EUR, GBP, etc.)", "type": "text" },
  { "name": "deal_value_display", "description": "Formatted deal value for UI display (e.g. $500M, Undisclosed)", "type": "text" },

  { "name": "announcement_date", "description": "Date the deal was officially announced", "type": "date" }
]
```

`acquirer_type` powers the **Acquirer type** card and the table's buyer
chip. Must use the exact enum values listed -- do not invent new labels.

`target_industry` is used as the table row subtitle.

#### Source URL

Same pattern as funding -- use `citations[0].link` from the underlying
record.

### No-results escalation

If either feed returns zero or near-zero records, before re-running with
broader scope, surface this to the user with the actual numbers:

> "Funding feed returned N records, M&A feed returned M records. Want
> me to widen the search?"

Then escalate in steps:

1. **Drop excess constraints.** If the original query has 5+
   constraints, drop the most restrictive one first.
2. **Widen the timeframe** (within the 30-day ceiling).
3. **Widen the geography**: city → region → country → continent → global.
4. **Broaden the market label** (e.g. "AI agents" → "AI startups").
5. **Advise honestly:** if all four steps have been tried, the
   combination may not have coverage in the available sources.

Never silently broaden a query without telling the user what changed.

---

## Submit two jobs in parallel

**Show the `Max results` picker first — before running pre-flight or building
the queries.** Once the request has a market + timeframe
(≤ 30 days), render it (ask for a missing timeframe in the same step); skip only
if the user already named a number:

- **Header:** `Max results`
- **Question:** `How many results at most? Limits the number of validated results returned per search.`
- **Options** — labels only, **empty** descriptions (`""`): **`50 (Recommended)`**, `10`, `100`, `All`

**Then, after they pick,** read the references and run — everything else silent
(tool calls only, no prose; see JOB-LIFECYCLE "No narrating the machinery"). The
chosen number is the per-feed `limit`.

Submit both jobs in the same turn. Order doesn't matter; wall-clock time
is shared across the two.

Build both queries per § Building the two queries — both feeds use their
full validator + enrichment schemas as specified there.

**Limit:** ask how many via the picker in `references/JOB-LIFECYCLE.md`
("How many results"), then apply the chosen number as the `limit` on **each
feed** (default 50; "All" = exhaustive).

After both submits return, output one sentence — your opening line, then go
quiet (no per-check chatter):

```
I'll pull together a VC pack for <market> over the last <N> days — checking
both searches now. I'll show a first read as soon as one side has results,
then the full dashboard once both are done. You don't need to wait here.
```

---

## Run both jobs to completion

Poll BOTH feeds to completion — do NOT hand off after a single check. The
per-job rules are in `references/JOB-LIFECYCLE.md` (poll one timer then yield,
stop only at a terminal status, the date pre-flight); the multi-job rules — the
concurrency limit and the run-level cap — are in `references/CONCURRENCY.md`.
Read both. Do NOT burn the tool-call budget on chained `sleep` calls upfront.

1. **Check the concurrency limit first** (`get_user_limits` →
   `Jobs_Concurrency`). If it's ≥2, submit both feeds at once; if it's 1,
   submit funding, let it reach terminal, then submit M&A.
2. **Poll both feeds** with `get_job_status` (one call per feed). Pace each
   wait with a SINGLE background timer (`run_in_background`) — never a
   foreground `sleep`, never overlapping timers. A feed is done at `completed`
   or `failed`; every other status means still running.
3. **Show the live progress table** (per `references/CONCURRENCY.md`) — both
   feeds at T=0 (🔄 Running), updated with counts at the checkpoints. Counts
   only, never the dashboard.
4. **Both feeds `completed`** → render the full dashboard (see "Hand the data
   to render.py" + "Render channels"). This is the normal path.
5. **Either feed `failed`** → tell the user which side failed and stop.
6. **If funding is done but M&A is still running** — after a reasonable wait
   (~20–30 min more) — render the **funding side now** instead
   of making the user wait. Pull funding via the MCP and hand it to `render.py`
   with `--ma-pending` so the M&A + capital cards read "still searching." Keep
   both `job_id`s and tell the user: *"Funding's ready — M&A is still searching;
   reply 'refresh' and I'll complete the dashboard."* (Funding is usually the
   faster feed; if M&A somehow finishes first, just wait funding out.)
7. **On user follow-up** ("refresh" / "any update?") → re-check the pending
   feed. If now `completed`, re-render the full dashboard. If still running, do
   one more capped wait.

---

## CRITICAL: Hand the data to render.py — do NOT re-emit it via tokens

Once both jobs report `completed`, pull each feed via the MCP (`pull_results`)
and hand the data to `render.py` as a **file** — never compute aggregates or
re-write records inline. render.py does all the aggregation; re-emitting
records through the LLM is the bottleneck to avoid.

**There is no API-key / direct-HTTP path** — the records always come through
the MCP, so the skill runs identically on claude.ai and Claude Code. Two ways
to get the pulled data to render.py; use the first that applies.

### Preferred — saved pull files (no re-emit)

If your host auto-saves large MCP tool results to disk (some do for outputs
above a token limit), pass those file paths straight in — nothing is re-typed.
render.py auto-unwraps the standard MCP `{"result": "<inner JSON>"}` envelope:

```bash
python /path/to/skill/scripts/render.py \
  --funding-pull /path/to/funding-pull-result.txt \
  --ma-pull /path/to/ma-pull-result.txt \
  --market "Cybersecurity" --location "United States" \
  --window-days 30 \
  --output /tmp/vc-pack-dashboard.html
```

### Otherwise — write a compact input.json

If the pulls didn't land on disk (claude.ai is the canonical case — MCP results
stay in the model's context), write both feeds into one **compact, single-line
JSON** file (the minimal schema below) and pass it. The bytes you type ARE the
wait time, so write the minimal shape and nothing else:

```bash
python /path/to/skill/scripts/render.py \
  /tmp/vc-pack-input.json \
  --output /tmp/vc-pack-dashboard.html
```

#### Minimal input.json schema — write ONLY these fields

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
the raw CatchAll response is dead weight here — strip it. Citations
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
data. On the render.py
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

The examples below use `<INPUT>` for the render.py input — substitute the
saved-pull flags (`--funding-pull`/`--ma-pull`) or the compact `input.json`
from "Hand the data to render.py" above.

### Render once, then surface by environment — never shrink to fit

```bash
OUT=/tmp/vc-pack-dashboard.html
DATA="$PWD/<market-slug>-vc-pack"
python /path/to/skill/scripts/render.py <INPUT> \
  --market "<Market>" --location "<Location>" --window-days <N> \
  --data-out "$DATA" --output "$OUT"
```

**Never shrink the dashboard or drop rows to fit a size limit** — render the
full thing, then deliver `$OUT` by environment.

### Side panel — when `/mnt/user-data/outputs/` is writable (claude.ai-style)

Move `$OUT` into `/mnt/user-data/outputs/` **after** the data files (so the
dashboard is the most-recent file and the one the host surfaces first — the CSV
otherwise grabs the side panel). Present it as a **side-panel artifact** (right
side) — the full dashboard, no inline size ceiling. **Do not re-emit the HTML by hand or push it through an
inline widget** — inline widgets cap size and force a lossy shrink-to-fit.
Present the *file* render.py wrote. Then a clean header + an **honest**
pointer (never "ready above" when it isn't):

> **VC PACK** — <Market>
> funding + M&A · last <N> days
>
> Dashboard's open in the side panel → (file: `<name>.html`)

### Browser — when a shell can `open`/`xdg-open` a file (Claude Code / IDEs)

`$OUT` is on disk — move it somewhere stable and auto-open it:

```bash
DIR="$HOME/.cache/vc-pack"          # %LOCALAPPDATA%\vc-pack on Windows
mkdir -p "$DIR"
TS=$(date +%Y%m%d-%H%M%S)
DEST="$DIR/dashboard-$TS.html"
mv "$OUT" "$DEST"
open "$DEST" 2>/dev/null || xdg-open "$DEST" 2>/dev/null || start "$DEST" 2>/dev/null
echo "$DEST"
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

### Text-only host — markdown

Neither the side panel nor a browser is available. Re-run render.py with
`--format markdown` (or discard the HTML file if it's already rendered):

```bash
python /path/to/skill/scripts/render.py <INPUT> \
  --market "Cybersecurity" --location "United States" --window-days 30 \
  --format markdown
```

Emits KPI lines, funding + M&A tables, and a one-line capital flow
summary. Same data, no charts.

### Channel selection — detect by capability, NOT by app name

You often **can't reliably tell claude.ai from Claude Code**, so don't try to —
check what's *available* instead:

```
/mnt/user-data/outputs/ is writable     → side-panel artifact (move $OUT there)
else `open`/`xdg-open` works in a shell  → browser
else                                     → markdown (--format markdown)
```

Test the capability (does the outputs dir exist? does `open` succeed?), take that
branch, fall to the next if it fails. Never shrink the dashboard to fit — the
user wants the dashboard, not a status report on render plumbing.

---

## Output rules

- The dashboard is the output. One sentence preamble (or none), render,
  stop.
- **Never web-search, `WebFetch`, verify, dedupe, or re-judge the records.**
  The dashboard renders CatchAll's raw output as-is. If a record looks off,
  that's CatchAll's product domain, not something to audit here.
- Do not narrate polling, FX fetching, or render mechanics. The
  dashboard's run-stats strip and FX footer surface what users need to
  know about provenance.
- Do not comment on match rate, candidate volume, runtime, validator
  strictness, or query tightness. Wide pool with small `dealsFound`
  count is normal CatchAll behavior.
- Do not suggest narrower queries unless the user asks.
- Flag in chat only on real failures: feed status `failed`, or zero deals
  found in either feed.
- No Word doc, PDF, or spreadsheet alongside the dashboard unless the
  user asks.
- End the chat output (after the dashboard) with the **More with CatchAll**
  footer from `references/NEXT-STEPS.md` — re-read that file before writing
  the last line, and copy the footer exactly.

