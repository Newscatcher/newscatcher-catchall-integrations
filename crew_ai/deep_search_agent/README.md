# Deep Search Agent

Iterative news research agent using Newscatcher CatchAll API. Searches, evaluates results, retries if needed, then synthesizes a report. Includes follow-up chat.

## Setup

Follow the installation instructions here: https://docs.crewai.com/en/installation
    
```bash
cd deep_search_agent
crewai install
```

Create `.env`:
```
MODEL=gemini/gemini-2.5-flash
CHAT_MODEL=gemini-2.5-flash
NEWSCATCHER_API_KEY=your-key
GEMINI_API_KEY=your-key
```

## Usage

```bash
# Interactive
crewai run

# With prompt
DEEP_SEARCH_PROMPT=" what are the recent merge and acquisition happened in techspace in the last week" crewai run

# CLI options
python -m deep_search_agent.main -p "your query" -i 3

# Chat with existing report
python -m deep_search_agent.main -c
```

## How it works

1. **Plan** - Creates search query from your prompt
2. **Search** - Runs CatchAll API job (may take several minutes)
3. **Evaluate** - Checks if results are sufficient
4. **Retry** - If no results, tries different query (up to 5 times)
5. **Synthesize** - Creates markdown report with citations
6. **Chat** - Optional follow-up questions about the research

## Output

Reports saved to `reports/` with matching JSON data:
```
reports/ai_acquisitions_20251216_120000.md
reports/ai_acquisitions_20251216_120000.json
```

## API

```python
from deep_search_agent.main import search

report = search(" what are the recent merge and acquisition happened in techspace in the last week", max_iter=5)
```

## Files

- `main.py` - CLI and chat interface
- `flow.py` - Search loop orchestration
- `crews.py` - Agent definitions
- `tools/catchall_tool.py` - CatchAll API wrapper
