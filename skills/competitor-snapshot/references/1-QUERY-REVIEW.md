# Query Review Reference

Before running any CatchAll job, confirm that the user's request is
specific enough to produce a useful, predictable result. Skills exist
to wrap CatchAll into easy invocations — but the skill must not burn
significant credits on ambiguous scope.

This file applies to **all CatchAll skills**. Individual skills can
add their own intake rules on top.

## When to ask the user vs. proceed with defaults

Ask the user to confirm before submitting any jobs when **any** of
the following is true:

1. **A critical parameter is missing** — most commonly, the time
   window. Without a window, results aren't reproducible and credits
   are spent on an arbitrary guess.
2. **An uploaded list exceeds the skill's per-run cap** (typically
   100 entities). Tell the user the cap, offer to proceed with the
   first N, and point them to the CatchAll platform + Book a demo
   links (see `4-NEXT-STEPS.md`) for larger lists.
3. **Estimated credit cost exceeds 25% of the user's remaining
   monthly credits** — pull `mcp__catchall__get_user_limits` to read
   `Monthly Granted Credits` and `current_usage`. If the estimated
   job set will eat a significant share, confirm.

Note: skills that use CatchAll's watchlist mode (`connected_dataset_ids`)
get the same record-cost for one company or many — the queries are
shared across the watchlist. Credits do NOT scale linearly with
entity count in those skills; only with records found. So multi-entity
scope alone is rarely the reason to confirm — the cost gate above
handles practical limits.

Proceed with defaults (without asking) when:

- All parameters are specified clearly
- Scope is single-entity AND the default cost is < 25% of remaining credits
- The user said "just run it" or similar explicit override

When in doubt, ask. One round-trip of confirmation costs nothing;
silently burning credits is hard to undo.

## What to ask, and how

Use `AskUserQuestion` in Claude Code for interactive chip-style
pickers. In other runtimes (claude.ai web, ChatGPT, Codex), fall back
to plain text asking and wait for the user's response.

### Standard time-window question

When the window is missing, ask:

> "How far back should I look for this query?"

Standard options:
- Last 7 days
- Last 14 days
- Last 30 days (the plan maximum for most users)
- Other (custom)

If the user picks a window beyond the plan's lookback limit, fall
back to the maximum the plan allows and note it.

**Waive-off default**: if the user explicitly declines to choose ("just
run it"), default to **last 7 days** — the cheapest standard window. A
waved-off run should not spend 30-days-of-credits on a scope the user
never stated. A skill whose target events are naturally sparse (e.g.
M&A, funding rounds) may set a longer waive-off default in its own
`SKILL.md`.

### Standard scope-confirmation question

When the skill is being run on multiple entities and credits will be
significant, ask:

> "This will run [N] CatchAll jobs across [E] entities, using roughly
> [C] credits ([P]% of your remaining monthly allowance). Should I
> proceed?"

Standard options:
- Proceed with all [E] entities
- Run on top [k] entities only (where k is some smaller number)
- Reduce the time window first
- Cancel

### Standard "ambiguous entity" question

When the user names an entity that could refer to multiple things
(e.g., "Apple" could be the tech company or the record label),
clarify before submitting:

> "Just to confirm, are you asking about [most likely interpretation],
> or [other plausible interpretation]?"

## How to estimate credit cost

Before asking the scope-confirmation question, estimate cost:

1. Read `Monthly Granted Credits` and `current_usage` from
   `get_user_limits`. Remaining = limit − current_usage.
2. Per CatchAll's pricing:
   - **Base mode**: ~10 credits per validated record (approximate;
     varies). Default limit (1000 records) ≈ 10,000 credits per job.
   - For a multi-bucket skill running B buckets × E entities:
     total_jobs = B × E, total_credits ≈ total_jobs × per-job-credits
3. Cap each job's `limit` based on remaining budget if needed (skills
   already do this — see SKILL.md guidance).

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
consistency across skills:

| Knob | What the skill should do |
|---|---|
| **Mode** | Always set to `"base"` (full pipeline). Surface in `meta.mode` in JSON and in the chat dashboard. |
| **Validators** | Don't pre-specify. Leave to CatchAll's auto-selection — auto-validators are a product feature. Pre-specifying defeats the point unless the user asked for a specific filtering rule. |
| **Company Watchlist** (`connected_dataset_ids`) | Only when the skill is built around a named entity list (e.g., supplier watchlist, customer list). Skip for free-form competitor or topic queries. |
| **Enrichments** | Always specify explicitly per bucket in the skill's `SKILL.md`. Without explicit enrichments, CatchAll auto-selects field names that drift between runs and the chat schema breaks. |
| **Search Depth** (`start_date` / `end_date`) | Derived from the user's time window. Clamp to plan limits via `initialize_query` — see `2-JOB-LIFECYCLE.md` § Pre-flight. |
| **Max Valid Results** (`limit`) | Default to **100 per query** (the agreed soft cap). If any bucket returns exactly 100 records, surface a "Showing 100 of N. Ask to load more." note in chat. When the user asks to load more, call `mcp__catchall__continue_job` with a higher limit (default jump: 500). The agent can further lower the initial limit below 100 if the credit budget is tight. |

If a skill needs additional configuration choices (e.g., per-bucket
validators or a specific watchlist), set them in that skill's `SKILL.md`,
not in this shared reference.

## Don't ask too much

Confirmation friction kills demo quality. Aim for at most one
confirmation prompt per run. If multiple parameters are unclear,
combine them into a single prompt (using `AskUserQuestion`'s multi-
question support) rather than serializing them.

If the user gives a fully-specified request the first time, do not
ask any confirmation questions — just run.
