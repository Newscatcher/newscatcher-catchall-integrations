# Extraction reference

Query construction, validators, and enrichments for the VC pack's two
feeds.

---

## CRITICAL: Never query for web pages

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

---

## Constraint cap (applies to both feeds)

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

---

## Funding job

### Query formula

`"<event verb> + <stage if specified> + <industry/market> + <location> + <timeframe>"`

Use natural language. CatchAll interprets it -- don't reduce to keywords.

| User intent | Query |
|---|---|
| AI agents funding last 7 days | `"funding rounds announced by AI agent startups in the last 7 days"` |
| Cybersecurity US last 30 days | `"funding rounds announced by cybersecurity companies in the United States in the last 30 days"` |
| Series B fintech Europe | `"Series B funding rounds announced by fintech companies in Europe in the last 30 days"` |

### Query signal terms (include at least one)

`raised, secures funding, closes round, announces investment, seed round,
Series A, Series B, funding announcement, backed by, led by`

### Valid funding events

- Officially announced closed/completed round
- Confirmed by the company, named investor, or credible source
- Amount or stage publicly disclosed

### Excluded

Rumors, funding targets, government grants, IPOs, SPACs, debt financing.

### Validators

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

### Enrichments

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

### Source URL

Use `citations[0].link` from the underlying record. Not in the
enrichment schema -- the citations list is populated by clustering, not
LLM extraction.

---

## M&A job

### Query formula

`"<target description> + <event verb> + <location> + <timeframe>"`

| User intent | Query |
|---|---|
| AI agents M&A last 7 days | `"AI agent companies that were acquired in the last 7 days"` |
| Cybersecurity US last 30 days | `"cybersecurity companies that were acquired or merged in the United States in the last 30 days"` |
| Healthcare AI Europe | `"healthcare AI companies that announced an acquisition in Europe in the last 30 days"` |

### Query signal terms (include at least one)

`acquires, acquired by, merges with, merger, takeover, asset purchase,
buys, deal closed, acquisition announced, acqui-hire, combines with`

### Valid M&A events

- Officially announced acquisition, merger, asset purchase, or acqui-hire
- Confirmed ownership transfer or merger announcement

### Excluded

Rumors, partnerships without ownership transfer, funding rounds, IPOs,
licensing deals, minority stakes.

### Validators

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

### Enrichments

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

### Source URL

Same pattern as funding -- use `citations[0].link` from the underlying
record.

---

## Limit

Set `limit: 50` on each VC pack job. This is enough for a 30-day market
view and bounds runtime. The user can request a higher limit
explicitly; otherwise stick to 50.

---

## No-results escalation

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
