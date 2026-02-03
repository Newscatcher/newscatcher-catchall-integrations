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
python claude_api_example.py
```

Or use in your own code:
```python
from claude_api_example import run_agent

response = run_agent("Find news about AI acquisitions in the last week")
```

## How it works

1. **User Query** - You provide a natural language request
2. **Tool Selection** - Claude decides which CatchAll tools to use
3. **Submit** - Calls `submit_query` to start a news search job
4. **Poll** - Calls `get_job_status` until job is completed
5. **Retrieve** - Calls `pull_results` to get clustered articles
6. **Synthesize** - Claude summarizes the results

## Available Tools

| Tool | Description |
|------|-------------|
| `submit_query` | Submit a natural language news search query |
| `get_job_status` | Check if a job is complete |
| `pull_results` | Get clustered and summarized articles |
| `list_user_jobs` | List all your previous jobs |
| `continue_job` | Continue a job that needs more data |

## Example Output

```
============================================================
User: Find recent news about AI startup funding rounds in the last 7 days
============================================================

🔧 Tool: submit_query
   Input: {"query": "AI startup funding rounds last 7 days"}
   Result: {"job_id": "abc123", "status": "submitted"}...

🔧 Tool: get_job_status
   Input: {"job_id": "abc123"}
   Result: {"status": "completed", "clusters": 15}...

🔧 Tool: pull_results
   Input: {"job_id": "abc123"}
   Result: {"clusters": [...]}...

============================================================
Assistant:
Based on my search, here are the recent AI startup funding rounds...
============================================================
```

## Configuration

You can customize the Claude model:

```python
run_agent("your query", model="claude-sonnet-4-20250514")  # Default
run_agent("your query", model="claude-opus-4-20250514")    # More capable
run_agent("your query", model="claude-haiku-3-5-20241022")   # Faster/cheaper
```

## API Keys

- **CatchAll API Key**: Get one at [newscatcherapi.com](https://www.newscatcherapi.com/)
- **Anthropic API Key**: Get one at [console.anthropic.com](https://console.anthropic.com/)
