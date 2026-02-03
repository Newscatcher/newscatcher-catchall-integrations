---
name: newscatcher-catchall
description: Search and analyze news articles using natural language queries via Newscatcher CatchAll API. Use when users ask for news research, market intelligence, competitive analysis, or current events monitoring.
license: MIT
compatibility: Requires NEWSCATCHER_API_KEY environment variable or api_key parameter. Network access to catchall.newscatcherapi.com required.
metadata:
  author: Newscatcher
  version: "1.0"
  api-docs: https://docs.newscatcherapi.com/
---

# Newscatcher CatchAll News Search

You have access to the Newscatcher CatchAll API for intelligent news research. This API searches 100,000+ news sources, clusters related articles, and generates summaries.

## When to Use

Activate this skill when users ask about:
- Recent news on any topic
- Market research or industry trends
- Competitive intelligence
- Company monitoring
- M&A activity, funding rounds, partnerships
- Current events or breaking news
- Media coverage analysis

## Available Tools

| Tool | Purpose |
|------|---------|
| `submit_query` | Submit a natural language news search query |
| `get_job_status` | Check if processing is complete |
| `pull_results` | Retrieve clustered articles and summaries |
| `list_user_jobs` | View previous searches |
| `continue_job` | Resume a job needing more data |

## Workflow

1. **Submit**: Call `submit_query` with the user's request. Returns a `job_id`.
2. **Poll**: Call `get_job_status` with the `job_id`. Repeat until status is `completed`.
3. **Retrieve**: Call `pull_results` with the `job_id` to get clustered articles.
4. **Summarize**: Present findings to the user.

## Query Guidelines

- Include time ranges: "last 7 days", "past month", "since January 2025"
- Be specific: "Tesla partnership announcements" not just "Tesla news"
- Use natural language: "companies acquiring AI startups" works well

## Example Queries

```
Find all M&A deals in the tech sector from the last 7 days
```

```
What news has been published about OpenAI in the past week?
```

```
Search for AI regulation news in Europe since January 2025
```

```
Find funding rounds for fintech startups in the last month
```

## Handling Results

Response from `pull_results` contains:

| Field | Description |
|-------|-------------|
| `job_id` | The job identifier |
| `query` | Original search query |
| `status` | Job status (e.g., "Job Completed") |
| `duration` | Processing time (e.g., "16m") |
| `candidate_records` | Total articles scanned |
| `valid_records` | Articles that passed validation |
| `date_range` | Object with `start_date` and `end_date` |
| `validators` | List of validation criteria used |
| `enrichments` | List of extracted data fields |
| `all_records` | Array of validated records |

Each record in `all_records` contains:

```json
{
  "record_id": "unique-id",
  "record_title": "Summary title of the event/story",
  "enrichment": {
    // Extracted structured data - varies by query type
    // Examples: deal_value, deal_type, acquired_company, etc.
    "confidence": "high"
  },
  "citations": [
    {
      "title": "Source article title",
      "link": "https://source-url.com/article",
      "published_date": "2026-01-30T14:25:04Z"
    }
  ]
}
```

When presenting results:
1. Summarize the total records found vs candidates scanned
2. Present key findings from the `record_title` and `enrichment` fields
3. Include source citations with links
4. Note the date range covered
5. Offer to search for related topics if needed

## Status Progression

Jobs progress through these states:
```
submitted → analyzing → fetching → clustering → enriching → completed
```

Poll `get_job_status` every few seconds until `completed`. Processing typically takes 30-120 seconds depending on query complexity.

## Error Handling

- If `submit_query` fails with auth error: Ask user to verify their API key
- If job stays in non-completed state: Use `continue_job` to resume
- If results are empty: Suggest broadening the query or time range
