# Claude Agent Integration

Use Newscatcher CatchAll API as tools with the Claude API (Anthropic SDK). Claude autonomously submits jobs, checks status, and retrieves results.

Two examples are included:

- **`claude_agent_example.py`** — Basic agent: jobs only (submit, poll, pull results).
- **`claude_agent_skill_example.py`** — Skill-based variant: loads the general-use-case CatchAll Skill as Claude's system prompt so Claude automatically applies query-writing rules, validators, and enrichment schemas. Also covers monitors.

## Setup

```bash
cd "Claude/Claude Agent"
pip install -r requirements.txt
```

Export environment variables:
```bash
export CATCHALL_API_KEY=your-catchall-key
export ANTHROPIC_API_KEY=your-anthropic-key
```

## Usage

```bash
# Basic agent
python claude_agent_example.py

# Skill-based agent (includes monitors, uses CatchAll Skill as system prompt)
python claude_agent_skill_example.py
```

Or use in your own code:
```python
from claude_agent_example import run_agent

response = run_agent("Find news about AI acquisitions in the last week")
```

## How it works

1. **User query** — You provide a natural language request
2. **Tool selection** — Claude decides which CatchAll tools to use
3. **Submit** — Calls `submit_query` to start a job (default: 10 records)
4. **Wait 30s** — System waits before the first pull
5. **Poll** — Calls `pull_results` to get records as they stream in
6. **Wait 1 min** — If job not complete, waits before the next poll
7. **Synthesize** — Claude summarizes the final results

## Available Tools

**Basic agent (`claude_agent_example.py`)**

| Tool | Description |
|------|-------------|
| `submit_query` | Submit a natural language query. Limits to 10 records by default. Set `fetch_all=true` only if the user explicitly asks for all results. |
| `pull_results` | Retrieve validated, enriched records (supports streaming) |
| `get_job_status` | Check job progress (shows X/6 steps completed) |
| `list_user_jobs` | List all previously submitted jobs |
| `continue_job` | Expand a job to process more records beyond the initial limit |

**Skill-based agent (`claude_agent_skill_example.py`)** — all of the above, plus:

| Tool | Description |
|------|-------------|
| `create_monitor` | Create a recurring monitor from a completed job |
| `list_monitors` | List all monitors |
| `pull_monitor_results` | Get latest aggregated monitor results |
| `enable_monitor` / `disable_monitor` | Start or pause a monitor |
| `update_monitor` | Update per-run record limit |

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
   📊 Progress: 3/6 steps completed
   📍 Current status: fetching

🔧 Tool: pull_results
   Input: {"job_id": "abc123"}
   📊 Got 5 records so far (status: clustering)
   ⏳ Job still processing. Waiting 1 minute before next poll...

🔧 Tool: pull_results
   Input: {"job_id": "abc123"}
   ✅ Job completed with 10 records

============================================================
Assistant:
Based on my search, here are the recent AI startup funding rounds...
============================================================
```

## Configuration

You can customize the Claude model:

```python
run_agent("your query", model="claude-sonnet-4-5")    # Default
run_agent("your query", model="claude-opus-4-5")      # More capable
run_agent("your query", model="claude-haiku-4-5-20251001")  # Faster/cheaper
```

## API Keys

- **CatchAll API Key**: Get one at [https://platform.newscatcherapi.com/](https://platform.newscatcherapi.com/)
- **Anthropic API Key**: Get one at [console.anthropic.com](https://console.anthropic.com/)
