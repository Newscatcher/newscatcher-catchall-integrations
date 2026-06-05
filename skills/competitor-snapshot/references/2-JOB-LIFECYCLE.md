# Job Lifecycle Reference

The canonical contract for submitting CatchAll jobs, detecting completion,
pulling results, and handling concurrency and plan limits. Any skill that
calls CatchAll MUST follow this pattern. Do not re-implement polling or
completion logic inside the skill body — drift between skills produces
silent-failure loops.

## Status states

Jobs progress linearly through these states:

| State | Phase | Terminal? |
|---|---|---|
| `submitted` | Queued | No |
| `analyzing` | Generating queries and validators | No |
| `fetching` | Retrieving web pages | No |
| `clustering` | Grouping into event clusters | No |
| `enriching` | Validating + extracting fields | No |
| `completed` | Final results ready | **Yes** |
| `failed` | Processing error | **Yes** |

**Stop polling if and only if `status ∈ {completed, failed}`** (or the
run-level 90-min cap fires — see § The completion algorithm). Every
other value means the job is still running, regardless of how long it's
been. Typical per-job duration is 10–15 minutes; tail latency can reach
30+ minutes for heavy queries. Total run wall-clock = ceil(N / concurrency) × per-job, so a 7-search run on concurrency=2 takes ~40–60 min total.

## Progress signals

These three fields come from `pull_results`, not `get_job_status`. They
indicate whether more records are still being produced:

| Field | Meaning |
|---|---|
| `candidate_records` | Total clusters discovered |
| `progress_validated` | How many clusters have been validated so far |
| `valid_records` | Clusters that passed all validators (subset of validated) |

**Invariants:**

- During `enriching`: `progress_validated < candidate_records` means more
  records may still appear.
- When `status == "completed"`: `progress_validated == candidate_records`.
  No more records will appear.
- Pagination fields (`page`, `page_size`, `total_pages`) describe records
  available **right now**, not the final count. A partial pull with
  `total_pages == 1` does NOT mean the job is done.

## The completion algorithm

```
1. Submit jobs in concurrency-sized waves. Capture job_id per bucket.
2. Note run_start (wall-clock when the first wave was submitted).
3. Poll every 60 seconds:
   a. Call get_job_status for each non-terminal job.
   b. If a job's status ∈ {completed, failed}, stop polling THAT job.
   c. After each wave fully terminates, submit the next wave.
   d. If total elapsed since run_start crosses 20, 40, or 60 minutes,
      render a progress checkpoint in chat (see § Progress reporting).
   e. If total elapsed since run_start crosses 90 minutes — STOP polling.
      Treat any non-terminal job as ⚠ Pending. Pull whatever exists.
4. Iterate page=1..total_pages with page_size=100 per completed job.
5. Verify len(collected) == valid_records per job. If short, sleep 10s
   and re-pull all pages once.
6. If status was "failed" on a bucket, surface the error in the artifact
   (run_flags), not the chat output. Use whatever partial data was retrieved.
7. Persist meta.per_bucket.<bucket>.job_id for every bucket, including
   any ⚠ Pending ones — the user may ping back and we'll re-poll those.
```

**The 90-minute hard cap is run-level, not per-job.** Never poll
indefinitely. Typical multi-bucket runs finish in 20–60 min (depending
on concurrency); a 90-min cap accommodates heavy runs while still
catching genuinely stuck states. After 90 minutes, the skill must
surface what it has plus ⚠ Pending markers for any unfinished bucket
— it does NOT kill the CatchAll-side job, it just stops polling.

### Re-poll on user follow-up

If the user pings back later (e.g. "any update on the search?") and
the JSON has any `⚠ Pending` buckets (their `meta.per_bucket.<bucket>.job_id`
is recorded), call `get_job_status` for each pending job_id. If now
`completed`, pull and atomically regenerate the JSON / CSV / xlsx
files, then render the closing table (all ✅) + a brief delta summary
("Financial signals: 6 → 11 events"). Don't re-render the entire
sectioned report unless the user asks for it.

## Concurrency: submit in waves

The plan caps how many jobs can run concurrently. Always query the limit
at the start of any multi-bucket skill — never assume:

| Operation | MCP | HTTP |
|---|---|---|
| Read plan limits | `mcp__catchall__get_user_limits` | `POST /catchAll/user/limits` |

Read the `Jobs_Concurrency` feature. Typical values:

| Plan | Concurrent jobs |
|---|---|
| Pay-as-you-go | 2 |
| Starter | 2 |
| Scale | 4 |
| Enterprise | Variable (negotiated) |

**Most users are on 2 concurrent slots.** Skills with more than 2 buckets
must submit in waves:

```
wave_size = min(num_buckets, concurrency_limit)
for batch in chunks(buckets, wave_size):
    submit_all_in_batch_in_parallel(batch)
    poll_each_to_terminal(batch)
    pull_each(batch)
```

**Never submit more jobs than the concurrency limit.** The API returns 403,
and the skill loses track of which buckets were dropped.

## Progress reporting (user-facing)

CatchAll runs take 20–60+ min wall-clock; users wait that whole time.
The chat interface **cannot update an already-printed message** — every
output is appended. So we render the **same table structure** at every
checkpoint, with status emojis and (after the first checkpoint) live
counts updating in place. To the reader it feels like one table being
updated, not many separate tables being thrown at them.

### Status values

| Symbol | Label | Meaning |
|---|---|---|
| ✅ Done | — | Search completed normally |
| 🔄 Running | — | Currently being polled |
| ⏳ Queued | — | Submitted-but-waiting, or not yet started |
| ⚠ Pending | — | 90-min cap hit; we stopped polling. Search may still be running on CatchAll's side. Re-pollable on user follow-up |
| ❌ Failed | — | CatchAll returned `status: failed` (see § Failure handling) |

Note: ⏳ Pending and ⚠ Pending differ by icon — ⏳ Queued means "not started", ⚠ Pending means "started, we stopped checking". The icon carries the distinction.

### Stage rows — derived from the run

Row labels are user-facing — drop CatchAll/dev terminology like "wave",
"bucket", "validator". The user just sees their query split into
N parallel searches.

- **Watchlist uploaded ([N] companies)** — only for watchlist runs (skip for non-watchlist skills)
- **Searching [Category]** — one row per search query (one per bucket in this skill). All start as ⏳ Queued except the first `concurrency` rows, which start as 🔄 Running
- **No "Build report" row** — local agent work that takes seconds. Hiding it keeps the table about CatchAll operations only

This pattern is consistent across all CatchAll skills.

### Render schedule

| When | What | Why |
|---|---|---|
| **T=0** (immediately after first wave submitted) | Opening one-liner + table | Sets expectations, shows the plan |
| **After each wave completes** | One-line plain text mentioning the categories that just finished and the categories starting next | Movement signal without table noise |
| **T=20 min** (if not done) | Update the table with current statuses + add columns `Web pages scanned` / `Events found` populated for any non-Queued rows. Offer "show partial". | First checkpoint — user might be tabbing away |
| **T=40 min** (if not done) | Same as T=20 update | Second checkpoint |
| **T=60 min** (if not done) | Same table update + escalated copy ("Taking longer than usual...") | Third checkpoint |
| **T=90 min** (hard cap) | Closing table with ⚠ Pending for unfinished searches + Files saved block + pending-search guidance + sectioned partial report | End of polling |
| **All searches complete** (before 90 min) | Closing table with all ✅ + Files saved block + full sectioned report | Normal completion |
| **User pings later with pending jobs** | Updated closing table (all ✅) + delta summary + Files updated block. Don't re-render the sectioned report unless asked | Follow-up after a cap |

### Opening one-liner — total-time estimate from concurrency

The one-liner personalizes the time estimate to the user's actual
`Jobs_Concurrency` (read in pre-flight). Formula:

```
waves         = ceil(num_jobs / concurrency)
total_min_lo  = waves * 10
total_min_hi  = waves * 15
```

Template (skip the watchlist clause for non-watchlist skills; include the concurrency clause only when `concurrency < num_jobs`, since users with enough slots to run everything in parallel don't have any "wait for slot" to explain):

```
[N companies uploaded.] [num_jobs] searches submitted — [your account can run [concurrency] searches at a time, so ]total wait is usually [total_lo]–[total_hi] min. I'll report back as it runs.
```

Wording notes:
- "your account can run N searches at a time" — plan-agnostic. We don't fetch plan name from `get_user_limits`, only the actual `Jobs_Concurrency` number. Reading the number directly is also accurate even if CatchAll has manually adjusted a user's concurrency outside their plan default
- Drop the "your account can run..." clause entirely when concurrency ≥ num_jobs — there's no waiting to explain

Per-plan examples for a 6-company, 7-search competitor-snapshot run:

| Concurrency | Waves | Total | One-liner output |
|---|---|---|---|
| 2 (typical PAYG / Starter) | 4 | 40–60 min | `6 companies uploaded. 7 searches submitted — your account can run 2 searches at a time, so total wait is usually 40–60 min. I'll report back as it runs.` |
| 4 (typical Scale) | 2 | 20–30 min | `6 companies uploaded. 7 searches submitted — your account can run 4 searches at a time, so total wait is usually 20–30 min. I'll report back as it runs.` |
| 7+ (e.g. some Enterprise) | 1 | 10–15 min | `6 companies uploaded. 7 searches submitted — usually 10–15 min total. I'll report back as it runs.` |

### Opening table — at T=0

Example with concurrency=2 (6-company foundation-labs run):

```
6 companies uploaded. 7 searches submitted — your account can run 2 searches at a time, so total wait is usually 40–60 min. I'll report back as it runs.

| Stage | Status |
|---|---|
| Watchlist uploaded (6 companies) | ✅ Done |
| Searching Product launches | 🔄 Running |
| Searching Pricing and packaging | 🔄 Running |
| Searching Leadership and hires | ⏳ Queued |
| Searching Customer wins | ⏳ Queued |
| Searching Partnerships and integrations | ⏳ Queued |
| Searching M&A and capital | ⏳ Queued |
| Searching Financial signals | ⏳ Queued |
```

### Between waves — one-liner with category names

When a wave's last job reaches terminal, print one plain-text line
naming the categories that just finished and the categories starting:

```
Product launches and Pricing and packaging done — starting Leadership and Customer wins.
```

No table. These keep the run from feeling frozen.

### Checkpoint tables — at T=20 / T=40 / T=60

Same row structure as the opening table, plus two columns:
`Web pages scanned` and `Events found`. Populate these for any
non-Queued row by reading `candidate_records` and `valid_records`
from `get_job_status` (no full pull needed — partial counts come from
status alone).

Checkpoint copy:

**T=20** (first):
```
Still working — usually wraps up 20–40 more min from here. If you want, you can follow live progress at https://platform.newscatcherapi.com/catchall/searches, or hang on and I'll update you.
```
Append below the table:
```
_If you want a preview of what's been found so far, just say "show partial"._
```

**T=40** (second):
```
Still working. You can follow live progress at https://platform.newscatcherapi.com/catchall/searches.
```
Also include the "show partial" italicized offer.

**T=60** (third):
```
Taking longer than usual. I'll keep waiting up to 30 more min. In the meantime:
- Follow the search live: https://platform.newscatcherapi.com/catchall/searches
- Reach out to CatchAll support: support@newscatcherapi.com
```
No "show partial" offer at T=60 — by now we're recommending the UI as the primary fallback.

Use generic language in checkpoint copy ("the search", "still working"). Do NOT name specific categories that are slow — the table shows specifics. Users only know they asked for a snapshot; they don't think in terms of individual category jobs.

### Closing table — normal completion

Same rows as opening / checkpoints, all ✅:

```
| Stage | Status | Web pages scanned | Events found |
|---|---|---|---|
| Watchlist uploaded (6 companies) | ✅ Done | — | — |
| Searching Product launches | ✅ Done | 306 | 57 |
| Searching Pricing and packaging | ✅ Done | 249 | 49 |
| ... |
| Searching Financial signals | ✅ Done | 161 | 11 |
```

Immediately follow the closing table with the skill's findings output.

### Closing table — 90-min cap hit

Same rows. Any non-terminal job is marked ⚠ Pending with its partial
counts and "(so far)" annotation in the Events column:

```
Stopped polling at 90 min — here's what I have. One search hadn't finished, and may still be running on CatchAll's side.

| Stage | Status | Web pages scanned | Events found |
|---|---|---|---|
| Watchlist uploaded (6 companies) | ✅ Done | — | — |
| Searching Product launches | ✅ Done | 306 | 57 |
| ... |
| Searching M&A and capital | ✅ Done | 340 | 12 |
| Searching Financial signals | ⚠ Pending | 95 | 6 (so far) |
```

Then a Files saved block + pending-search guidance:

```
**Files saved:**
  xlsx: <absolute path>
  JSON: <absolute path>
  CSV:  <absolute path>

**One search hadn't finished when I stopped polling:**
- Financial signals — job ID `<uuid>`

**What you can do:**
1. Follow this search in the CatchAll UI: https://platform.newscatcherapi.com/catchall/searches
2. Ping me again later — I'll fetch the latest results from the same job
3. Contact CatchAll support: support@newscatcherapi.com (reference the job ID above)
```

Then the standard sectioned report with whatever data was pulled. Any
section corresponding to a ⚠ Pending search gets a "(partial — search
still pending)" note in its section header.

### Follow-up — user pings back, ⚠ Pending search has completed

When the user pings ("any update on the search?"), and re-polling shows
the pending job is now `completed`:

```
The Financial signals search finished. Pulled the results and updated the files.

| Stage | Status | Web pages scanned | Events found |
|---|---|---|---|
| Watchlist uploaded (6 companies) | ✅ Done | — | — |
| ... |
| Searching Financial signals | ✅ Done | 161 | 11 |

**What's new since the partial report:**
- Financial signals: 6 → 11 events (5 new), 95 → 161 web pages scanned
- Events worth watching: 17 → 19 (2 new entries from Financial signals)

**Files updated:**
  xlsx: <absolute path>
  JSON: <absolute path>
  CSV:  <absolute path>

Want me to re-render the full report in chat, or just the Financial signals section?
```

Don't re-render the entire sectioned report unless the user asks. The files are the source of truth and they're already updated.

## No helper scripts

Do not write `.py` (or other) orchestration scripts to run the skill.
Helper scripts are the single biggest source of run-time overhead:
they cause debug-fix-retry cycles, stale intermediate files, and turn
a clean run into a debugging session.

The approved orchestration pattern, every step done directly:

| Operation | How |
|---|---|
| Upload a watchlist (`/datasets/upload`) | MCP dataset tool if the CatchAll MCP exposes one, otherwise one `curl` command (multipart) — see `COMPANY-WATCHLIST.md` § Execution path. |
| Submit a query **with `connected_dataset_ids`** | `mcp__catchall__submit_query` if it accepts a watchlist parameter, otherwise one `curl` command per query — see `COMPANY-WATCHLIST.md` § Execution path. |
| Submit a query **without** a dataset | `mcp__catchall__submit_query` |
| Poll job status | `mcp__catchall__get_job_status` (needs only the job_id) |
| Pull results | `mcp__catchall__pull_results` (needs only the job_id) |
| Merge results, write JSON / CSV | `Write` tool + inline reasoning — hold results in context, no merge script |
| Build the xlsx workbook | Inline Python via `Bash` using `openpyxl` (install with `pip install openpyxl --break-system-packages` if missing). The xlsx build IS a script — but a focused, single-purpose one that runs once at the end of the run from the in-memory results. This is the one exception to the "no helper scripts" rule, because xlsx generation needs a real library |

A short inline bash loop for repetitive `curl` submits is fine. A
standalone script file that orchestrates the whole run is not.

## Pre-flight: MCP and API key

Before submitting any jobs — and before any user-facing output beyond
the intake questions — verify the CatchAll MCP is wired up and the API
key is configured. This catches the two common failure modes cheaply,
before the user has waited.

**Step 1 — Is the MCP installed?** Check the available tools for any
`mcp__catchall__*` tool. If none exists, the MCP isn't installed in this
runtime. Tell the user and stop — do not try to substitute `curl`:

> The CatchAll MCP isn't connected in this session. Install it
> (https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart),
> then restart and try again.

**Step 2 — Is the API key configured?** Call `mcp__catchall__get_user_limits`.
If it returns `Error: API key is required.`, the MCP is wired but no key.
Point the user at the platform and stop:

> The CatchAll MCP is installed but no API key is configured. Get a key at
> https://platform.newscatcherapi.com/ and set it as `CATCHALL_API_KEY` (env
> var) or as `x-api-key` in your MCP config, then try again.

If `get_user_limits` succeeds, you also have `Jobs_Concurrency` (needed
for wave sizing in § Concurrency) and `Monthly Granted Credits` /
`current_usage` (needed for the cost gate in `1-QUERY-REVIEW.md`) — one
call covers all three, no extra round trip.

A failed pre-flight always stops the skill **before** any submits. The
worst failure mode is letting the user wait 30 minutes and then hitting
"Error: API key is required" mid-run.

## Pre-flight: lookback bounds

The plan caps how far `start_date` can reach back. **The boundary is a
timestamp, not a date.** If the plan allows 31 days and the current moment
is `2026-05-20 09:06:38`, the cutoff is `2026-04-19 09:06:38`. Submitting
`start_date=2026-04-19` returns a 400.

Plan lookback windows (also discoverable via `get_user_limits`):

| Plan | Lookback |
|---|---|
| Pay-as-you-go / Starter | 1 month |
| Scale | 3 months |
| Enterprise | Variable |

**Two safe patterns:**

1. **Recommended**: call `initialize_query` before submitting. It returns
   the effective `start_date` / `end_date` after plan clamping, plus a
   `date_modification_message` explaining any adjustment. Use the returned
   values verbatim.
2. **Fallback if you can't initialize**: clamp `start_date` to
   `today - (lookback_days - 1)` so it's safely inside the plan window.

Do not silently re-submit with `+1 day` adjustments hoping to get past the
boundary. Use the documented pre-flight.

## Partial pulls (opt-in only)

`pull_results` does work before terminal status, but **do not use partial
pulls by default**. Wait for terminal status (`completed` or `failed`),
then do the full paginated sweep.

Use partial pulls only when the user explicitly asks for early or
preliminary results. In that case:

- Pull with `page=1`, present what you have, note clearly that the job
  is still running and numbers may change.
- Keep polling.
- Re-pull only when the user requests fresher data, or at terminal status.

Partial pulls do not consume extra capacity, but they create UX risk —
preliminary counts shift as more records validate, and presenting them
as final misleads the user.

## Failure handling

| Failure | Response |
|---|---|
| `status == "failed"` | Pull once to capture partial data. Surface error in the artifact's `run_flags`, not the chat. Do not auto-retry. |
| 400 on submit (lookback) | Re-run the pre-flight check. Don't keep nudging dates by one day. |
| 403 on submit (concurrency) | Wait for one in-flight job to reach terminal, then submit. |
| 422 on submit (validation) | Surface to the user — the skill author has a bug. |
| Job stuck in `fetching` >5 min | Keep polling. This is documented as normal. |
| **Run hits 90-min cap with any non-terminal jobs** | Stop polling. Mark non-terminal jobs ⚠ Pending. Surface the closing table + Files saved + pending-search guidance (see § Progress reporting → Closing table — 90-min cap hit). Do not auto-retry. |

The 90-min cap is the run-level safety net — see § The completion
algorithm. Per-bucket job_ids for any ⚠ Pending searches are persisted
in `meta.per_bucket.<bucket>.job_id` so re-poll on user follow-up
works automatically.

## Common failure modes — DO NOT do these

These patterns have produced silent loops or lost work in past skill runs.
They are forbidden in any CatchAll skill.

- **Custom bash polling loops with `grep` on the status JSON.** A regex
  typo silently disables the exit condition; the loop spins until externally
  killed. Use the MCP tool. If you must use HTTP, parse with `jq`, never
  with `grep -o`.
- **`run_in_background: true` on a poll-until-condition loop in Claude Code.**
  The harness only notifies on process exit. If the exit condition never
  fires, the harness never wakes the agent. Use foreground polling.

  **Fine in background**: fixed-duration commands like `sleep 90 && echo done`
  always exit on the timer and reliably notify. The forbidden pattern is
  specifically `until` / `while` loops whose exit depends on a condition
  firing — those can spin silently if the condition has a bug.
- **Polling faster than every 60 seconds.** Documented cadence is 30–60s.
  Standardize on 60s — faster polling burns rate limit without benefit.
- **Submitting more jobs than the concurrency limit and hoping the API
  queues them.** It doesn't — it 403s.
- **Computing `start_date = today - N days` without checking plan limits.**
  Will 400 if N exceeds the plan's lookback. Use `initialize_query` or clamp.
- **Treating partial-pull `total_pages` as final.** During `enriching`,
  pagination only reflects records validated so far.
- **Hardcoding concurrency=2 or =4 in the skill body.** Always read it
  from `get_user_limits` at runtime. Enterprise plans can have higher
  values; assuming 2 wastes capacity, assuming 4 produces 403s.

## Prefer MCP tools over HTTP when available

If the runtime has the `catchall` MCP server installed (Claude Code with
the catchall MCP config), **use MCP tools, not HTTP**:

| Operation | MCP tool | HTTP equivalent |
|---|---|---|
| Submit job | `mcp__catchall__submit_query` | `POST /catchAll/submit` |
| Check status | `mcp__catchall__get_job_status` | `GET /catchAll/status/{job_id}` |
| Pull results | `mcp__catchall__pull_results` | `GET /catchAll/pull/{job_id}` |
| Initialize | `mcp__catchall__initialize_query` | `POST /catchAll/initialize` |
| Plan limits | `mcp__catchall__get_user_limits` | `POST /catchAll/user/limits` |
| Continue job | `mcp__catchall__continue_job` | `POST /catchAll/continue` |

MCP tools return parsed JSON. No shell quoting, no regex on response
bodies, no string-parsing failure modes. Every bash polling failure
documented above stems from falling back to curl when MCP was available.

If the runtime only has HTTP access (no MCP), use HTTP with a JSON-aware
parser (`jq`, Python `json`, etc.), never `grep` on response bodies.
