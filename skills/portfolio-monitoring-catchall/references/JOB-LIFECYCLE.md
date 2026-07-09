# Job Lifecycle

The contract for running **one** CatchAll search (or one feed) to
completion: submit, wait, surface progress, deliver.

## How CatchAll reports progress: polling only

There is **no push.** For a single search, CatchAll exposes three endpoints —
`POST /catchAll/submit` → `GET /catchAll/status/{job_id}` → `GET /catchAll/pull/{job_id}`
— and the only way to learn a job's state is to GET the status endpoint.
No webhooks, callbacks, server-sent events, or blocking/long-poll exist for
one-off jobs. (Webhooks exist only for *Monitors* — scheduled recurring
queries that push to a server you host — which is a different feature and
not used by a user-run skill.)

**So "stay quiet" is an _output_ policy, not a _polling_ policy.** Keep
polling silently in the background; just print nothing to the chat between
milestones. It has to work this way: the skill auto-shows a partial batch and
auto-delivers the final result, and both are only possible while it keeps
polling. Stop polling and the user would have to ask for every update.

## Status states

| State | Meaning | Terminal? |
|---|---|---|
| `submitted` | Queued | No |
| `analyzing` | Generating queries + validators | No |
| `fetching` | Retrieving web pages | No |
| `clustering` | Grouping pages into events | No |
| `enriching` | Validating + extracting fields (partial results available here) | No |
| `completed` | Final results ready | **Yes** |
| `failed` | Processing error | **Yes** |

**Stop polling only at `completed` or `failed`.** Every other value —
including `enriching` — means it's still running, no matter how long it's
been; there is **no time cap**. Typical run is 10–15 min; heavy queries can
sit in `enriching` for 30+ min.

## Polling — pace yourself, host-aware

How you wait between status checks depends on whether your host **re-invokes you
when a background task finishes**. Get this wrong and the run either spins or
silently stops.

**Host that wakes you on background-task completion** (Claude Code, Cursor,
IDEs): `run_in_background` hands control straight back, so don't spin — start
**one** background timer (a single `sleep` ~180s, `run_in_background`), then
**end your turn and write nothing**; the completion notification brings you back
to call `get_job_status` once, then repeat. **Exactly one timer at a time** —
stacking them is the #1 polling failure.

**Turn-based host with no background wake-up** (claude.ai and similar): **do NOT
end your turn to wait — nothing re-invokes you, and the run silently stops.**
Keep the poll loop *inside one turn*: `get_job_status` → pace → check again,
until terminal. Pacing the gap with a background timer is fine — what's fatal is
**ending the turn** to wait for one (you can't foreground-`sleep`, but that does
NOT mean you should yield; stay in-turn and keep polling). **Hand off *before*
you run low on tool calls — not after.** If a run is clearly going to outlast the
turn (a heavy feed, checks piling up), stop and hand off cleanly while you still
can: _"Still running — reply 'refresh' and I'll pull the results."_ Running *out*
of tool calls mid-poll — no result, a confusing half-answer — is the failure to
avoid. The user's "refresh" is a fresh turn, so a clean hand-off + ping always
finishes; even a long run completes over a couple of pings.

Either way: **one wait at a time, ~60–180s between checks, first check ~1–2 min
after submit**, and never end the turn expecting a wake-up your host doesn't
send. (A host Monitor/until tool, where available, is also fine.)

## The waiting contract — what the user sees (and doesn't)

This is the part the user feels. **Your first visible output is the `Max
results` picker** (or, if the count was already given, the opening line in beat
1). Everything before it — loading the skill, reading references, pre-flight —
stays silent: **tool calls only, no prose** (see "No narrating the machinery").
After the opening line, **speak only at the milestones below; between them, poll
silently and send nothing to the chat.**

**1. Opening (T=0) — your first message, then go quiet.** Say it's running,
give an honest estimate, and that they don't need to wait:
> On it — this usually takes **~10–20 min**; I'll keep you posted. You don't need to wait here.

**2. First solid batch — shown ONCE, automatically.** Watch `valid_records`
on each poll; when it first crosses a meaningful threshold (≥5, or the first
batch on a small-limit run), pull once and show that batch, clearly labeled:
> Here's a first partial batch — [n] results so far. Still searching; I'll
> post the complete set when it's done.

Show this **once** — don't re-prompt for "more" or keep posting partials.

**3. Completion — deliver the full set automatically.** At `completed`, pull
all pages (verify you collected `valid_records` records; if short, wait ~10s
and re-pull all pages once) and render the skill's normal output. The full set
supersedes the partial; the user doesn't have to ask.

**4. If the user asks mid-run** — one short status line, no internals:
> Still searching — about [m] min in, usually wraps by ~[t]. You can watch it
> live at platform.newscatcherapi.com/catchall/searches, or hang on — I'll
> drop the results here automatically the moment they're ready.

**Long runs — check in, don't cap.** There is no time cap; poll to
completion, however long it takes. If the search is still running at ~30 min,
post one neutral check-in line, and repeat roughly every 30 min:
> Still searching — [n] events found so far. You can watch it live at
> platform.newscatcherapi.com/catchall/searches, or hang on — I'll keep you
> posted.

From the second check-in on, also offer support: _"…or reach
support@newscatcherapi.com if you think something's off."_ Never imply the
run is slow or that something is wrong — the check-in is an option, not an
alarm.

## Detecting the partial (you derive it — nothing is pushed)

`status` / `pull` return `candidate_records` (clusters found),
`progress_validated` (validated so far), and `valid_records` (passed all
validators). There is no "first result ready" event — you detect the partial
milestone by watching these cross a threshold while polling. Pulling before
`completed` is supported and costs no extra capacity — but a partial pull's
pagination (`total_pages`) only reflects records validated **so far**, never
the final count.

## How many results — the `Max results` picker

The skill asks this as its **first output** — a multiple-choice picker, before
reading references or building the query (the exact copy + options live in the
skill's run steps, so it renders without reading anything first). Skip it only
if the user already named a number. The chosen number is the `limit`: a
**per-search** ceiling, so each search returns **up to** that many validated
records, never more — default **50**. If the user wants more after delivery, use
`continue_job` to extend the SAME job — never resubmit.

## Never present partial data as final

Only `completed` results are final; partial counts shift as more records
validate. The auto-shown partial in beat 3 is always labeled as such. Never
ship `enriching` data as the finished answer (e.g. "1 deal found" when dozens
are still validating).

## No narrating the machinery — hard rule

Do **not** surface internal processing to the user: no setup/pre-flight
play-by-play (e.g. "let me check the skill", "Pre-flight passes"), no
validated/candidate counts, no stage names, no "progress is slow", no
"delivering current results as the count stabilized", no caveats about the skill
itself, no fact-checking CatchAll's own output. The user asked for results, not a job monitor. The only
user-facing messages are the templated ones above plus the final results.

## Re-poll on user follow-up

If the user pings back later ("any update?" / "refresh") and you have a kept
`job_id`, call `get_job_status` for it. If now `completed`, pull and deliver
the final results plus a one-line "what changed" note. If still running, do
one more capped wait.

## Pre-flight (before submitting)

1. **MCP installed?** Check for a CatchAll MCP tool. The connector prefix
   varies by host, so match on the `CatchAll`/`catchall` substring — e.g.
   `mcp__claude_ai_CatchAll__get_user_limits` (claude.ai) or
   `mcp__catchall__get_user_limits` (a local config). If none exists, tell the
   user the CatchAll MCP isn't connected and point them to the setup guide —
   `https://www.newscatcherapi.com/docs/web-search-api/integrations/mcp` (it
   covers getting an API key too) — then stop. Do not substitute curl.
2. **API key set?** Call that `get_user_limits` tool. If it returns
   `Error: API key is required.`, point the user to that same setup guide
   (`https://www.newscatcherapi.com/docs/web-search-api/integrations/mcp`) to
   add their key, and stop.
3. **Dates valid?** Set `end_date` to **today** (the API rejects a future
   `end_date`) and `start_date` to today − (window − 1), within the plan's
   lookback — get them right on the **first** submit. Do this **silently**:
   **never surface the plan's lookback window or any date clamp.** A
   "lookback window (31 days)" shown next to a 7-day request reads as if the
   agent misunderstood — to the user there is only their requested window.

A failed pre-flight stops the skill before any submit — the worst outcome is
making the user wait, then erroring.

## Failure handling

| Failure | Response |
|---|---|
| `status == "failed"` | Pull once for partial data, tell the user the search failed, do not auto-retry. |
| 400 on submit (dates) | `start_date` beyond lookback, or `end_date` in the future — clamp (`end_date` ≤ today, `start_date` within window) and resubmit **silently**. |
| 403 on submit (concurrency) | Wait for an in-flight job to reach terminal, then submit. |
| Stuck in `enriching` unusually long | Still running — keep polling, with the ~30-min check-ins (live link, then support). |

## Prefer MCP tools over HTTP

If the CatchAll MCP is available, use the MCP tools — they return parsed JSON.
The tool names below are shown **unprefixed**; call them under whatever prefix
your host exposes (`mcp__claude_ai_CatchAll__…` on claude.ai, `mcp__catchall__…`
on a local config). **Pass only the parameters listed below; an extra or
renamed field is rejected as "invalid tool parameters" (the CatchAll MCP has
~55 similar tools, so don't borrow a param from a sibling):**

- `get_job_status(job_id)` — `job_id` is the only argument.
- `pull_results(job_id)` — plus optional `page` / `page_size` for pagination;
  nothing else.
- `continue_job(job_id, limit)` — extend the same job at a higher limit; never
  resubmit.
- `get_user_limits()` — no arguments (the key resolves from config).
- `submit_query(query, …)` — `query` required; optional `start_date`,
  `end_date`, `limit`, `mode`, `validators`, `enrichments`,
  `connected_dataset_ids`. Validators are type `boolean` only; enrichment
  `type` is one of `text` / `number` / `date` / `option` / `url` / `company`.

If the MCP isn't available, stop per pre-flight — never hand-write your
own HTTP calls in place of these tools.
