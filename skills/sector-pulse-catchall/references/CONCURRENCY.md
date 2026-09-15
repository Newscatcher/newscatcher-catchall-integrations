# Concurrency Add-on — running many searches at once

For skills that submit several CatchAll searches in parallel (e.g. two feeds, or
a watchlist run across N categories). This **extends `JOB-LIFECYCLE.md` (CORE)**
— per-search mechanics (quiet wait, the picker, deliver, failure handling) are
unchanged. What's different when many run at once: submit in waves, **no time
cap**, and the **live progress table** below — the multi-job form of CORE's
auto-partial. A parallel run shows progress as a table of counts, **never one
search's results as if they were the whole.**

## Read the concurrency limit first

The plan caps how many jobs run at once. Read it at the start — never assume:
`get_user_limits` → the `Jobs_Concurrency` feature (commonly 2; Scale ~4;
Enterprise varies).

## Submit in waves

```
wave_size = min(num_searches, concurrency_limit)
for each wave:
    submit all searches in the wave in parallel
    poll each to terminal (per CORE)
    submit the next wave
```

Never submit more than the limit at once — the API returns 403 and you lose
track of which searches were dropped.

## No time cap — let it finish, surface help without alarm

There's **no time cap** — let every search run to terminal, however long it
takes. The risk
isn't runtime, it's the user wondering if it's stuck. So as it runs long, keep
the table updating and make the monitoring options **available** — never
implying it's slow:
- **live view** (`platform.newscatcherapi.com/catchall/searches`) — they watch
  each search move there;
- **support** (`support@newscatcherapi.com`) — if they suspect something's
  actually wrong.

Frame these as _"here's where you can watch it / reach out if you're
concerned"_ — **never** _"this is taking too long / longer than usual."_ Keep
every `job_id` so a later "refresh" re-polls. (A job that never terminates is a
failure — surface it as ❌ in the table, not a timeout you announce.)

## The live progress table

The user may wait anywhere from tens of minutes to a few hours, and the chat
can't edit a printed message, so render the **same table at each checkpoint** — to the reader it feels like one table
updating, not many. One row per search, **labelled in the user's terms** (the
skill's feeds / categories — "Funding", "M&A", "Pricing"). In every
user-facing message a unit of work is a **search** — never "bucket",
"wave", or "job 1"; those words stay out of the chat entirely. The
first `concurrency` rows start 🔄 Running, the rest ⏳ Queued. (A watchlist skill
adds a top `Watchlist uploaded (N companies) ✅ Done` row; others omit it. No row
for local file-building — the table is about CatchAll searches only.)

**Status icons:** ✅ Done · 🔄 Running · ⏳ Queued · ⚠ Pending (results were
delivered while it was still running; re-pollable) · ❌ Failed.

### T=0 — opening line + kickoff table

Open with **one tight line** — what you're doing + window, a **generous** time
estimate (bold it), and "I'll keep you posted" — then the table. Render this
opening on **every** multi-search run — a single-company run across N
categories included; never skip it. Don't describe the table or the run
mechanics; they surface on their own.

> `On it — [what], [window]. This usually takes **~[estimate]**; I'll keep you posted. You don't need to wait here.`

Pick the estimate from waves (`waves = ceil(searches / concurrency)`) but **err
high** — one search runs ~10–25 min and **wider windows run longer**, so round
up rather than risk a low number that makes a healthy run look stuck:

- **1 wave** → ~10–30 min · **2–3 waves** → ~30–90 min · **4+ waves / big
  watchlist** → _"a few hours"_ (don't pin a number)

```
On it — a VC pack for fintech, last 7 days. This usually takes **~10–30 min**; I'll keep you posted. You don't need to wait here.

| Search | Status |
|---|---|
| Funding | 🔄 Running |
| M&A | 🔄 Running |
```

(A 4-wave run reads the same with a wider estimate — _"…This usually takes **an
hour or more**; I'll keep you posted…"_ — first two rows 🔄, the rest ⏳.)

### Between waves (only if >1 wave)

When a wave's last job goes terminal, one plain-text line — no table — naming
what finished and what's starting: _"Funding done — starting M&A."_ Skip this
entirely when everything ran in one wave.

### Checkpoints — re-render at intervals while it runs

Every ~15 min it's still going, re-render the same table plus two columns,
`Web pages scanned` and `Events found`, filled for any non-Queued row from
`candidate_records` / `valid_records` on `get_job_status` (no full pull needed).
Keep the copy **neutral and un-alarmed** — never "slow," "taking longer than
usual," or naming a lagging search (the table shows the specifics):

- **Early on** — _"Still searching — here's where it stands. You can watch each
  search live at platform.newscatcherapi.com/catchall/searches, or hang on and
  I'll keep updating."_
- **Longer in** — _"Still going — a multi-search run takes a while. Live view:
  platform.newscatcherapi.com/catchall/searches; or reach
  support@newscatcherapi.com if you think something's off."_

The link and support are **available options**, not a signal anything's wrong.

### Closing table

Same rows, all ✅ with the counts filled, then hand straight to the skill's
normal deliverable (findings / dashboard / files). If the user asks for what's
in so far (or a search failed), mark unfinished rows ⚠ Pending with `(so far)`
counts, add a Files-saved block + the unfinished `job_id`s + the live link, and
note any partial section — so a later "refresh" completes it.

## Re-poll on follow-up

If any search is ⚠ Pending, re-poll its `job_id` on the user's next message
and deliver a short delta (e.g. _"Financial signals: 6 → 11"_). Per-search
`job_id`s must be persisted for this to work.
