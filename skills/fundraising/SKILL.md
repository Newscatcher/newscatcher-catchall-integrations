---
name: catchall-fundraising
description: Invoke this skill for any query about startup or company funding
 announcements -- pre-seed, seed, Series A, Series B, Series C, and beyond.
 Triggers on queries like "Series B raises in Austin last 30 days", "which
 AI startups raised seed funding this month", "funding rounds in Europe last
 2 weeks". Works for any geography, any funding stage, and any industry
 vertical. This is an event-based skill reusable across GTM, VC, recruiting,
 and market intelligence use cases. Do NOT invoke for government grants,
 IPOs, debt financing, or rumored raises.
---

This skill finds structured event records about company funding announcements.
It solves two things: how to write the right query, and what data to extract
from results. CatchAll returns events extracted from web pages -- not raw web
pages themselves. Every query, validator, and enrichment must reflect this
distinction. You are describing funding events, not requesting journalism.

---

## CRITICAL: Never query for web pages

Before constructing any query, run this self-check:

**Does my query contain any of these forbidden phrases?**

- `news articles`, `news stories`, `articles about`, `stories about`
- `press coverage`, `media coverage`, `NLP summary`
- `recent news`, `news on`, `coverage of`, `reports on`
- `find articles`, `search articles`, `get articles`

If yes -- **stop and rewrite**. The query must describe what happened
in the world, not what was written about it.

**Wrong:** `"news articles about Series B raises in Austin last 30 days"`
**Right:** `"Series B funding rounds announced in Austin in the last 30 days"`

**Wrong:** `"find articles covering seed funding in fintech startups"`
**Right:** `"seed funding rounds announced by fintech startups in the last 14 days"`

Validators and enrichments must also be event-scoped. Never write a
validator like `"web page mentions a funding round"` -- write
`"a company has officially announced a closed or completed funding round"`.

---

## How to build a query

Write a natural language sentence that describes the real-world event,
not a keyword string. CatchAll processes natural language and will
interpret it -- you do not need to reduce it to search keywords.

**Formula: describe what happened + 2-4 specifics**

The required specifics for funding events are:
1. **Event type** -- the funding announcement (raise, round, funding, investment)
2. **Funding stage** -- optional, only if the user specified one (seed, Series A, Series B, etc.)
3. **Location** -- city, region, country, or global; if not specified, runs globally
4. **Timeframe** -- explicit window within 30 days ("last 14 days", "last 30 days"); never open-ended ("since January")
5. **Industry or company type** -- optional, only if the user specified one

**Examples:**

| User input | Query to build |
|---|---|
| "Series B raises in Austin last month" | `"Series B funding rounds announced by companies in Austin in the last 30 days"` |
| "AI startups that raised seed this week" | `"seed funding rounds announced by AI startups in the last 7 days"` |
| "who raised money in fintech last 2 weeks" | `"funding rounds announced by fintech companies in the last 14 days"` |
| "funding rounds in Europe" | ask the user for a timeframe, then build: `"startup funding rounds announced in Europe in the last 30 days"` |


**Constraint limit:** Cap your query at 4 meaningful constraints. More than that and results will silently return nothing — CatchAll can't match a 6-way intersection that rarely appears in a single source.

The constraints most likely to kill results are qualifiers that don't appear in the announcement itself:
- Investor fund size ("led by a Tier 1 VC", "top-tier investor")
- Founder demographics ("female founders", "minority-owned")
- Ownership type ("bootstrapped", "non-VC-backed")

These are safe to include — they're almost always disclosed in the announcement:
- Funding amount threshold ("over $10M", "under $5M")
- Round stage ("Series A", "seed")
- Industry or company type ("fintech startup", "AI company")
- Location ("in Austin", "in Europe")


If the user has not provided a timeframe, ask before building the query -- a query without one will produce unreliable results. If no location is specified, the query runs globally.

**Timeframe window:** Max 30 days per query. For longer requests, split into consecutive 30-day windows and run each as a separate job.

---

## What counts as a valid funding event

A result qualifies only if it meets one of these criteria:

- The company has officially announced a closed or completed funding round
- An investment has been confirmed by the company, a named investor, or a credible source
- A funding amount and/or round stage has been publicly disclosed

These do not qualify:

- Rumors or unconfirmed reports ("reportedly raising")
- Funding targets or goals without a confirmed close ("seeking to raise")
- Government grants, subsidies, or non-equity funding
- IPOs, SPACs, or public market transactions
- Debt financing, loans, or credit facilities

The key test: has the round been officially confirmed as closed or announced by the company or a named investor? If not, exclude it.

---

## Standard validators

Use all four for every fundraising query. These are a strong starting point -- adjust as needed for your specific use case:

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

---

## Standard enrichments

These are a strong starting point -- add, remove, or edit based on your specific use case.

Core fields (used in UI table preview):

```json
[
 { "name": "company_name", "description": "Name of the company that raised funding", "type": "text" },
 { "name": "funding_round", "description": "Original stage label as reported (e.g. Series B2, Seed Extension)", "type": "text" },
 { "name": "funding_amount_display", "description": "Formatted funding amount for display (e.g. $5M, €3.2M, Undisclosed)", "type": "text" },
 { "name": "announcement_date", "description": "Date the funding round was officially announced or confirmed", "type": "date" }
]
```

Full enrichment schema:

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

 { "name": "investors", "description": "Named lead investors or participating firms, if disclosed", "type": "text" },
 { "name": "company_location", "description": "City, region, or country where the company is headquartered", "type": "text" },
 { "name": "industry_vertical", "description": "Industry or sector: fintech, AI, healthtech, SaaS, etc.", "type": "text" },
 { "name": "funding_purpose", "description": "Stated use of funds if mentioned: product development, market expansion, hiring, etc.", "type": "text" },

 { "name": "employee_count_range", "description": "Estimated company size: 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+", "type": "text" },
 { "name": "is_venture_backed", "description": "True if institutional investors (VC firms) are mentioned. null if unclear and only false when explicitly confirmed as bootstrap/non-VC-backed.", "type": "boolean" }
]
```

**Note on funding_amount:** Amount is split into three fields -- value (number), currency (text), and display (text). This prevents currency loss when amounts are in EUR, GBP, or other non-USD currencies, and gives the UI a pre-formatted string to render directly without reconstruction.

**Note on source URL:** Source URL is intentionally not in the enrichment schema. Use `citations[0].link` from the underlying record. The citations list is populated by the clustering pipeline (real URLs that were crawled), not LLM-extracted, so it's reliable. UIs can render it with a "+N more" indicator using `citations.length`.

---

## Extraction rules

When extracting enrichment fields from event records, follow these rules:

- Only extract confirmed, completed funding rounds. Exclude rumors, targets, grants, IPOs, and debt financing.
- Do not guess or infer missing values -- return null.
- `funding_amount_value`: extract numeric value only (e.g. 5000000).
- `funding_amount_currency`: extract currency code separately (USD, EUR, GBP).
- `funding_amount_display`: preserve original format where possible (e.g. "$10M", "€3.2M", "Undisclosed").
- `funding_stage_normalized`: map to pre-seed, seed, series_a, series_b, series_c, growth, or unknown.
- `announcement_date`: normalize to ISO format YYYY-MM-DD.
- `employee_count_range`: map to 1-10, 11-50, 51-200, 201-500, 501-1000, or 1000+.
- `is_venture_backed`: true if institutional investors are named. False if unclear or not stated.

---

## Query signal terms

Include at least one of these phrases in your CatchAll query to signal
that you are looking for funding events, not general company news:

 raised, secures funding, closes round, announces investment,
 seed round, Series A, Series B, funding announcement,
 backed by, led by

These are distinct from the company type or industry -- both should
appear in the query where relevant. Example:

 `"fintech startup raises Series A funding in London last 14 days"`

---

## Limit heuristics

| User intent | Example | Action |
|---|---|---|
| Exhaustive ("all", "every") | "Find all seed raises in Europe last month" | Omit `limit` |
| Exploratory | "What startups raised Series B last 30 days?" | Set `limit: 50` |
| Specific/narrow | "Any AI raises in Austin this week?" | Set `limit: 10` |

---

## Building follow-up query packages

If the user runs the query package and reports no results, produce a new package with a broader scope. Escalate in steps and explain which parameter you are widening before presenting the new package.

**Step 0 -- Check for over-constraining.**
Count the meaningful constraints in the original query. If there are 5 or more, drop the most restrictive one before widening anything else — prioritize removing qualifiers that rarely appear in funding announcements themselves (investor tier, founder demographics, ownership type).

Tell the user: "The query may have been too narrow. Here's a version with [dropped constraint] removed — try this before widening the timeframe or geography.

**Step 1 -- Expand the timeframe.**
If the original window was shorter than 30 days, build a new query using "last 30 days". Tell the user: "Here's a wider query covering the last 30 days instead of [N] days."

**Step 2 -- Expand the geography.**
Widen location by one level:
- city → metro area or region
- region → country
- country → continent or global

Tell the user: "Here's a query expanded to [broader area] since [original location] returned nothing."

**Step 3 -- Broaden the funding stage.**
If the original query targeted a specific stage, build a new query using a broader range ("any venture funding round"). Tell the user: "Here's a broader query covering all funding stages instead of [specific stage]."

**Step 4 -- Broaden the industry.**
If the original query targeted a specific vertical, remove the industry filter and run for all company types. Tell the user: "Here's a query without the [industry] filter to widen the scope."

**Step 5 -- Advise honestly.**
If the user has worked through all four fallback packages and still reports no results: "There may be limited coverage for this combination of parameters in the available sources. No further widening is likely to help."

Always explain what changed between the original and the follow-up package so the user can decide whether the broader scope suits their needs before running it.

---

## Architecture note

This skill is event-based, not persona-specific. The same skill is reused across:

- GTM pack -- fundraising + product-launches + local-business-openings
- VC pack -- fundraising + mergers-and-acquisitions
- Recruiting -- fundraising + hiring signals

Persona logic belongs in the package layer, not inside this skill.
