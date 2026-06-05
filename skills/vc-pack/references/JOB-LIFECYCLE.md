# Job Lifecycle Reference

How to run a single CatchAll job to completion: submit, poll, handle a slow
or stuck job, and deliver. Any skill that calls CatchAll MUST follow this
pattern — improvised polling loops are the main cause of stuck or
no-result runs. (The VC pack runs TWO jobs — apply these per-job rules to
each feed; see the skill's "Run both jobs to completion" section for the
two-feed coordination.)

## Status states

A job moves linearly through these states:

| State | Meaning | Terminal? |
|---|---|---|
| `submitted` | Queued | No |
| `analyzing` | Generating queries + validators | No |
| `fetching` | Retrieving web pages | No |
| `clustering` | Grouping pages into events | No |
| `enriching` | Validating + extracting fields | No |
| `completed` | Final results ready | **Yes** |
| `failed` | Processing error | **Yes** |

**Stop polling a feed only when its status is `completed` or `failed`** (or
the 90-min cap below fires). Every other value — including `enriching` —
means the job is still running, no matter how long it's been. Typical run
is 10–15 min; heavy queries can sit in `enriching` for 30+ min or longer.

## Polling — paced, and sleep-safe

1. First `get_job_status` check ~1–2 min after submit, then every ~60–90s.
2. **Do not poll in a tight loop**, and **do not use a foreground `sleep`** —
   some environments block bare `sleep` outright. To pace the wait, start
   ONE fixed-duration timer as a background command (`run_in_background`,
   e.g. a 60–90s wait), let it finish, then check status once, and repeat.
3. **Never start a new timer before the previous one returns**, and never
   leave several overlapping timers running — that produces the messy
   "leftover polling timer" output and loses track of state.
4. If the host exposes a Monitor/until tool, that is also fine for waiting.
   The invariant is: ~60–90s between checks, one wait at a time.

## The 90-minute cap

Never poll forever. If a job has not reached `completed` within ~90 min of
submit:

- Stop polling that job.
- Mark it ⚠ still-running and keep the `job_id`.
- Deliver whatever the skill can with what completed, **clearly labeled as
  preliminary**, and tell the user they can ping back to refresh.

This does NOT cancel the job on CatchAll's side; it just stops you waiting.

## Never present partial data as final

`pull_results` returns data during `enriching`, but those counts shift as
more records validate. **Only `completed` results are final.** Do not pull
mid-`enriching` data and present it as the finished answer — that silently
ships an incomplete dataset. Pull early only if the user explicitly asks,
and label it preliminary.

## Re-poll on user follow-up

If the user pings back later ("any update?" / "refresh") and you have a
⚠ still-running `job_id`, call `get_job_status` for it. If now `completed`,
deliver the final results. If still running, do one more capped wait.

## Pre-flight (before submitting)

1. **MCP installed?** Check for any `mcp__catchall__*` tool. If none exists,
   tell the user the CatchAll MCP isn't connected and stop — do not
   substitute curl.
2. **API key set?** Call `mcp__catchall__get_user_limits`. If it returns
   `Error: API key is required.`, tell the user to set a key and stop.

A failed pre-flight stops the skill before any submit — the worst outcome is
making the user wait, then erroring.

## Failure handling

| Failure | Response |
|---|---|
| `status == "failed"` | Tell the user that feed failed, do not auto-retry. |
| 400 on submit (lookback) | `start_date` exceeds the plan's window — clamp to within ~30 days and resubmit. |
| 403 on submit (concurrency) | Wait for an in-flight job to reach terminal, then submit. |
| Stuck in `enriching` past the cap | Treat as ⚠ still-running (see the 90-min cap). |

## Prefer MCP tools over HTTP

If the `catchall` MCP is available, use the MCP tools (`submit_query`,
`get_job_status`, `pull_results`, `get_user_limits`) — they return parsed
JSON. Only fall back to HTTP if there is no MCP, and then parse with a JSON
tool (`jq`/Python), never `grep` on the response body.
