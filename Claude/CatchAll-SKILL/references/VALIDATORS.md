# Validators Reference

Validators are boolean filters that decide whether a fetched article counts as a
valid record. They are the most important lever for controlling result quality
and cost in CatchAll.

## Why validators matter

**You pay per valid record.** Every article that passes all validators becomes a
billable record in your results. If your validators are too broad, the job will
match a large number of articles, run for a long time, and cost significantly
more. Well-crafted validators keep your results tight and your costs predictable.

## Schema

Validators are always boolean — they answer a yes/no question about each article.

```json
{
  "name": "is_about_ma_deal",
  "description": "True if the article describes a specific merger or acquisition deal, not general industry commentary",
  "type": "boolean"
}
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Short identifier for the validator (snake_case recommended) |
| `description` | Yes | Natural language rule defining what makes an article relevant |
| `type` | Yes | Always `"boolean"` |

## Writing good descriptions

The `description` is where you define relevance. The system uses it to evaluate
each article, so precision here directly affects result quality and cost.

**Be specific about what counts:**

```json
{
  "name": "is_about_ma_deal",
  "description": "True if the article reports on a specific, named merger or acquisition deal between two identified companies. False for general M&A trend pieces, market commentary, or analyst speculation.",
  "type": "boolean"
}
```

**Be explicit about what doesn't count:**

```json
{
  "name": "involves_pharma",
  "description": "True only if at least one party in the deal is a pharmaceutical, biotech, or life sciences company. False for healthcare IT, medical devices, or hospital systems.",
  "type": "boolean"
}
```

**Bad descriptions — too vague, will over-match:**

- `"Is this relevant"` — relevant to what?
- `"About pharma"` — any mention of pharma, or a pharma company must be central?
- `"M&A deal"` — does rumor count? Does a rejected bid count?

## Validators vs. date range (`start_date` / `end_date`)

These serve different purposes and work together:

| Mechanism | What it controls | Scope |
|---|---|---|
| `start_date` / `end_date` | Which time window of articles the system **searches through** in the database | Database query scope |
| Validators | Whether each individual article **qualifies** as a valid record | Per-article filtering |

The date range defines *where we look*. Validators define *what we keep*.

### Example 1 — Recent events with matching dates

**Query**: "Find all M&A in pharma industry for the last 7 days"

```json
{
  "query": "Find all M&A in pharma industry for the last 7 days",
  "start_date": "2026-02-01T00:00:00Z",
  "end_date": "2026-02-08T00:00:00Z",
  "validators": [
    {
      "name": "is_about_ma_deal",
      "description": "True if the article reports on a specific merger or acquisition deal",
      "type": "boolean"
    },
    {
      "name": "is_event_in_last_7_days",
      "description": "True if the M&A deal was announced or closed within the last 7 days from now",
      "type": "boolean"
    },
    {
      "name": "involves_pharma",
      "description": "True if at least one party is a pharmaceutical or biotech company",
      "type": "boolean"
    }
  ]
}
```

Here the date range and the event validator align — both cover the last 7 days.
The date range limits which articles we search; the validator confirms the *event
itself* happened in that window.

### Example 2 — Historical events, limited database access

**Query**: "Find all M&A of tech companies in 2025"

```json
{
  "query": "Find all M&A of tech companies in 2025",
  "start_date": "2026-01-25T00:00:00Z",
  "end_date": "2026-02-08T00:00:00Z",
  "validators": [
    {
      "name": "is_about_ma_deal",
      "description": "True if the article reports on a specific merger or acquisition deal",
      "type": "boolean"
    },
    {
      "name": "is_event_in_2025",
      "description": "True if the M&A deal was announced or closed at any point during the year 2025",
      "type": "boolean"
    },
    {
      "name": "involves_tech",
      "description": "True if at least one party is a technology company",
      "type": "boolean"
    }
  ]
}
```

This is where the distinction matters most. The user wants deals from all of 2025,
but their CatchAll plan may only provide access to the last 14 days of articles.
So:

- `start_date` / `end_date` is set to the last 14 days (the available database window)
- The validator `is_event_in_2025` is broader — it checks whether the *deal itself*
  happened in 2025, regardless of when the article was published

This works because news articles often reference past events. An article published
today might report on a deal that closed in March 2025. The date range finds the
article; the validator confirms the underlying event matches.

### Summary

```
Database window (start_date/end_date)
  → "Search articles published in this time range"

Validators
  → "From those articles, keep only the ones where the EVENT matches my criteria"
```

The date range is constrained by your CatchAll plan's historical access. Validators
have no such constraint — they evaluate content, not publication dates.

## Cost control tips

1. **Start narrow, then broaden.** Begin with strict validators and a short date
   range. Review the results. If you're missing relevant records, loosen one
   validator at a time.

2. **Use multiple validators as a filter chain.** Every article must pass *all*
   validators to become a record. Three specific validators are better than one
   vague one.

3. **Explicitly exclude noise.** If your topic attracts irrelevant articles (e.g.
   stock price commentary when you want deal announcements), add a validator that
   filters them out:
   ```json
   {
     "name": "is_not_stock_commentary",
     "description": "True only if the article discusses the deal itself, not stock price movements, analyst ratings, or portfolio updates",
     "type": "boolean"
   }
   ```

4. **Use `/initialize` to preview.** The initialize endpoint suggests validators
   before you commit. Review them — if they look too broad, tighten the
   descriptions before submitting.

5. **Set a `limit` during exploration.** While refining validators, use a `limit`
   to cap how many records you process. Once the validators are dialed in, remove
   the limit or create a monitor for the full run.

## Common validator patterns

| Use case | Validator name | Description |
|---|---|---|
| Event recency | `is_event_recent` | True if the event occurred within the specified time window |
| Industry filter | `involves_pharma` | True if a pharma/biotech company is directly involved |
| Event type | `is_acquisition` | True if the article describes an acquisition specifically, not a partnership or licensing deal |
| Noise exclusion | `is_not_opinion` | True if the article is a news report, not an opinion piece or editorial |
| Geographic filter | `is_us_based` | True if at least one party is headquartered in the United States |
| Significance | `is_deal_over_100m` | True if the reported deal value exceeds $100 million |