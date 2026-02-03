# Using Claude with Newscatcher CatchAll API

This guide shows how to use Claude (Desktop, Web, or API) with the Newscatcher CatchAll API for intelligent news research.

## What is CatchAll?

CatchAll is Newscatcher's agentic news search API. Give it a natural language query, and it will:
- Search across 100,000+ news sources worldwide
- Cluster related articles together
- Generate summaries for each cluster
- Return structured, deduplicated results

## Setup Options

### Option 1: Claude Desktop (MCP Server)

Install the MCP server for local use with Claude Desktop.

**Install:**
```bash
pip install git+https://github.com/Newscatcher/newscatcher-catchall-mcp.git
```

**Configure Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "newscatcher": {
      "command": "python",
      "args": ["-m", "server"],
      "env": {
        "NEWSCATCHER_API_KEY": "your-api-key"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see the Newscatcher tools available.

---

### Option 2: Claude Web (Remote MCP)

Connect to a hosted MCP server directly from Claude.ai.

**Add Remote MCP:**
1. Go to Claude.ai Settings → MCP Servers
2. Add server URL: `https://your-deployed-server.com/mcp?apiKey=YOUR_KEY`

Or deploy your own using [FastMCP](https://github.com/jlowin/fastmcp):
```bash
pip install fastmcp
fastmcp deploy server.py --name newscatcher-catchall
```

---

### Option 3: Claude API (Direct Integration)

For programmatic use, see the [Claude API example](./Claude%20API/README.md) which uses tools directly without MCP.

---

## How to Use

Once connected, simply ask Claude to search for news. Claude will automatically:
1. Submit your query
2. Wait for processing to complete
3. Retrieve and summarize results

### Example Prompts

**Market Research:**
```
Find all M&A deals in the tech sector from the last 7 days
```

**Competitive Intelligence:**
```
What news has been published about Tesla in the past week?
```

**Industry Trends:**
```
Search for news about AI regulation in Europe
```

**Event Monitoring:**
```
Find coverage of the latest Fed interest rate decision
```

**Company Monitoring:**
```
Get recent news about Apple's supply chain
```

### Advanced Prompts

**Comparative Analysis:**
```
Search for news about both OpenAI and Anthropic from the last month,
then compare their recent announcements
```

**Sentiment Analysis:**
```
Find news about Bitcoin from the past week and analyze
whether coverage is generally positive or negative
```

**Multi-topic Research:**
```
I need a briefing on three topics:
1. Electric vehicle sales in China
2. Semiconductor supply chain updates
3. Renewable energy investments in Europe
Search for each and give me a summary
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `submit_query` | Start a news search with natural language |
| `get_job_status` | Check if your search is complete |
| `pull_results` | Get the clustered articles and summaries |
| `list_user_jobs` | View your previous searches |
| `continue_job` | Resume a job that needs more data |

---

## Workflow

```
You: "Find news about AI startups raising funding"
        │
        ▼
   ┌─────────────┐
   │submit_query │ → Returns job_id
   └─────────────┘
        │
        ▼
   ┌─────────────┐
   │get_job_status│ → Polls until "completed"
   └─────────────┘
        │
        ▼
   ┌─────────────┐
   │ pull_results │ → Returns clustered articles
   └─────────────┘
        │
        ▼
Claude summarizes the results for you
```

---

## Tips

1. **Be specific with time ranges** - "last 7 days" or "past month" helps focus results

2. **Use natural language** - CatchAll understands queries like "news about company X partnering with company Y"

3. **Ask for analysis** - After getting results, ask Claude to identify trends, compare coverage, or extract key facts

4. **Iterate** - If results aren't what you expected, refine your query and search again

5. **Check job history** - Use `list_user_jobs` to revisit previous searches without re-running them

---

## Get API Key

Sign up at [newscatcherapi.com](https://www.newscatcherapi.com/) to get your API key.

---

## Resources

- [MCP Server Repository](https://github.com/Newscatcher/newscatcher-catchall-mcp)
- [Claude API Example](./Claude%20API/)
- [Newscatcher Documentation](https://docs.newscatcherapi.com/)
