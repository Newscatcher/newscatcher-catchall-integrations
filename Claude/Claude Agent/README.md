# Claude API Integration

Use Newscatcher CatchAll API as tools with Claude API (Anthropic SDK). Claude autonomously searches for news, checks job status, and retrieves results.

## Setup

```bash
cd "Claude/Claude API"
pip install -r requirements.txt
```

Create `.env` or export environment variables:
```bash
export CATCHALL_API_KEY=your-catchall-key
export ANTHROPIC_API_KEY=your-anthropic-key
```

## Usage

```bash
# Run the example
python claude_agent_example.py
```

Or use in your own code:
```python
from claude_agent_example import run_agent

response = run_agent("Find news about AI acquisitions in the last week")
```

## How it works

1. **User Query** - You provide a natural language request
2. **Tool Selection** - Claude decides which CatchAll tools to use
3. **Submit** - Calls `submit_query` to start a news search job (default: 10 results)
4. **Wait 30s** - System waits 30 seconds before first pull (streaming)
5. **Poll** - Calls `pull_results` to get partial results as they stream in
6. **Wait 1 min** - If job not complete, waits 1 minute before next poll
7. **Synthesize** - Claude summarizes the final results

## Available Tools

| Tool | Description |
|------|-------------|
| `submit_query` | Submit a news search query. Limits to 10 results by default. Set `fetch_all=true` only if user explicitly asks for ALL results. |
| `pull_results` | Get clustered articles (supports streaming) |
| `get_job_status` | Check job progress (shows X/7 steps completed) |
| `list_user_jobs` | List all your previous jobs |
| `continue_job` | Continue a job that needs more data |

## Example Output

```
============================================================
User: Find recent news about AI startup funding rounds in the last 7 days
============================================================

🔧 Tool: submit_query
   Input: {"query": "AI startup funding rounds last 7 days"}
   ⏳ Job submitted. Waiting 30 seconds before first pull...

🔧 Tool: get_job_status
   Input: {"job_id": "abc123"}
   📊 Progress: 3/7 steps completed
   📍 Current status: fetching

🔧 Tool: pull_results
   Input: {"job_id": "abc123"}
   📊 Got 5 clusters so far (status: clustering)
   ⏳ Job still processing. Waiting 1 minute before next poll...

🔧 Tool: pull_results
   Input: {"job_id": "abc123"}
   ✅ Job completed with 10 clusters

============================================================
Assistant:
Based on my search, here are the recent AI startup funding rounds...
============================================================
```

## Result Limiting

By default, queries are limited to **10 clusters** for faster results. Claude will only fetch all results when you explicitly ask:

```python
# Limited to 10 results (default)
run_agent("Find news about AI startups")

# Fetches ALL results (user must be explicit)
run_agent("Find ALL news about AI startups")
run_agent("Get everything about the Tesla announcement")
```

## Configuration

You can customize the Claude model:

```python
run_agent("your query", model="claude-sonnet-4-20250514")  # Default
run_agent("your query", model="claude-opus-4-20250514")    # More capable
run_agent("your query", model="claude-haiku-3-5-20241022") # Faster/cheaper
```

## API Keys

- **CatchAll API Key**: Get one at [https://platform.newscatcherapi.com/](https://platform.newscatcherapi.com/)
- **Anthropic API Key**: Get one at [console.anthropic.com](https://console.anthropic.com/)
