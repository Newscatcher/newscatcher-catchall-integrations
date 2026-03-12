# Validators Reference

Validators are boolean filters that decide whether a fetched article counts as a
valid record. They are the most important lever for controlling result quality
and cost in CatchAll.

## Why validators matter

**You pay per valid record.** Every article that passes all validators becomes a
billable record. Too-broad validators = more noise, longer runs, higher cost.
Well-crafted validators keep results tight and costs predictable.

## Schema

```json
{
  "name": "is_about_ma_deal",
  "description": "True if the article describes a specific merger or acquisition deal, not general industry commentary",
  "type": "boolean"
}
```

## Writing good descriptions

**Be specific about what counts:**
```json
{
  "name": "is_about_ma_deal",
  "description": "True if the article reports on a specific, named merger or acquisition deal between two identified companies. False for general M&A trend pieces, market commentary, or analyst speculation.",
  "type": "boolean"
}
```

**Explicitly exclude noise:**
```json
{
  "name": "involves_pharma",
  "description": "True only if at least one party in the deal is a pharmaceutical, biotech, or life sciences company. False for healthcare IT, medical devices, or hospital systems.",
  "type": "boolean"
}
```

## Validators vs. date range

| Mechanism | What it controls |
|---|---|
| `start_date` / `end_date` | Which time window of articles the system **searches** |
| Validators | Whether each article **qualifies** as a valid record |

Date range = where we look. Validators = what we keep.

**Key insight for historical queries**: Your CatchAll plan may only provide access
to recent articles (e.g. last 14 days), but articles published recently often
*reference* past events. Set `start_date`/`end_date` to your available window,
then write a validator that checks whether the *event itself* happened in the
target period — regardless of when the article was published.

## Cost control tips

1. **Use multiple validators as a chain** — every article must pass *all* validators.
2. **Start narrow, then broaden** — strict validators first, loosen if too few results.
3. **Exclude noise explicitly** — add a validator that filters out stock commentary, opinion pieces, etc.
4. **Use `/initialize` to preview** — check suggested validators before committing.
5. **Set a `limit` during exploration** — cap records while refining; remove limit for full runs.

## Common validator patterns

| Use case | Name | Description |
|---|---|---|
| Event recency | `is_event_recent` | True if the event occurred within the specified time window |
| Industry filter | `involves_pharma` | True if a pharma/biotech company is directly involved |
| Event type | `is_acquisition` | True if the article describes an acquisition specifically, not a partnership or licensing deal |
| Noise exclusion | `is_not_opinion` | True if the article is a news report, not an opinion piece or editorial |
| Geographic filter | `is_us_based` | True if at least one party is headquartered in the United States |
| Significance | `is_deal_over_100m` | True if the reported deal value exceeds $100 million |