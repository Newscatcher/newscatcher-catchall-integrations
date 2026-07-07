# Query Review Reference

Before running any CatchAll job, confirm that the user's request is
specific enough to produce a useful, predictable result.

## When to ask the user vs. proceed with defaults

Ask the user to confirm before submitting any jobs when **any** of
the following is true:

1. **A critical parameter is missing** — most commonly, the time
   window. Without a window, results aren't reproducible.
2. **A named entity or parameter is ambiguous** — see the standard
   "ambiguous entity" question below.

Proceed with defaults (without asking) when:

- All parameters are specified clearly
- The user said "just run it" or similar explicit override

When in doubt, ask. One round-trip of confirmation costs nothing.

## What to ask, and how

Ask as a multiple-choice picker where the host supports one
(arrow-select); fall back to a plain-text question elsewhere. Combine
with the `Max results` picker (`JOB-LIFECYCLE.md` § How many results)
in the same step, **time window first, then Max results** — at most one
confirmation prompt per run.

### Standard time-window question

When the window is missing, ask:

> "How far back should I look for this query?"

Options — labels only, empty descriptions, in this order:
**`Last 7 days (Recommended)`**, `Last 14 days`, `Last 30 days`. (30 days
is the plan maximum for most users; a typed custom window also works.)

If the user picks a window beyond the plan's lookback limit, fall
back to the maximum the plan allows — silently (see `JOB-LIFECYCLE.md`
§ Pre-flight: never surface the lookback window or any date clamp).

**Waive-off default**: if the user explicitly declines to choose ("just
run it"), default to **last 7 days** — the cheapest standard window. A
skill whose target events are naturally sparse (e.g. M&A, funding
rounds) may set a longer waive-off default in its own `SKILL.md`.

### Standard "ambiguous entity" question

When the user names an entity that could refer to multiple things
(e.g., "Apple" could be the tech company or the record label),
clarify before submitting:

> "Just to confirm, are you asking about [most likely interpretation],
> or [other plausible interpretation]?"

## When to suggest a monitor

If the user is asking the same question on a recurring basis (e.g.,
"competitive brief on these 5 companies every week"), suggest setting
up a CatchAll monitor instead of running the skill each time. Monitors
are cheaper for recurring scope and deduplicate across runs.

Only suggest this if the user mentions recurrence. Don't push monitors
on one-off queries.

## CatchAll configuration defaults — what skills set vs. what to leave to auto

Every `submit_query` call has several configuration knobs (visible in
the CatchAll web UI as the Configuration panel: Mode, Validators,
Company Watchlist, Enrichments, Search Depth, Max Valid Results). For
consistency:

| Knob | What the skill should do |
|---|---|
| **Mode** | Always set to `"base"` (full pipeline). Surface in `meta.mode` in JSON and in the chat dashboard. |
| **Validators** | Leave to CatchAll's auto-selection by default. When the skill's `SKILL.md` defines validators, use those exactly. |
| **Company Watchlist** (`connected_dataset_ids`) | Only when the skill is built around a named entity list. Skip for free-form topic queries. |
| **Enrichments** | Always specify explicitly, as the skill's `SKILL.md` defines them (per query, feed, or bucket). Without explicit enrichments, CatchAll auto-selects field names that drift between runs and the chat schema breaks. |
| **Search Depth** (`start_date` / `end_date`) | Derived from the user's time window. Clamp to plan limits via `initialize_query`, silently — see `JOB-LIFECYCLE.md` § Pre-flight. |
| **Max Valid Results** (`limit`) | The `Max results` picker (`JOB-LIFECYCLE.md` § How many results), applied per search. If a search returns exactly the chosen cap, surface a "Showing [cap] of [N]. Ask to load more." note in chat; on request, call `continue_job` with a higher limit. |

If a skill needs additional configuration choices (e.g., per-bucket
validators or a specific watchlist), set them in that skill's `SKILL.md`,
not in this reference.

## Don't ask too much

Aim for at most one confirmation prompt per run. If multiple parameters
are unclear, combine them into a single prompt rather than serializing
them.

If the user gives a fully-specified request the first time, do not
ask any confirmation questions — just run.
