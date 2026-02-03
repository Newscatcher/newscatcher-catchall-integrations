# CatchAll MCP Server

Connect to the Newscatcher CatchAll API via Model Context Protocol (MCP). This allows AI assistants to search and analyze news articles using natural language queries.

## Public MCP Server

**URL:** `https://catchall-mc.fastmcp.app/mcp`

**Source Code:** [github.com/Newscatcher/newscatcher-catchall-mcp](https://github.com/Newscatcher/newscatcher-catchall-mcp)

## Getting Your API Key

Get your CatchAll API key at [platform.newscatcherapi.com](https://platform.newscatcherapi.com/)

---

## Claude Code

Claude Code supports MCP servers via CLI or settings file.

### Option 1: CLI Command

```bash
claude mcp add catchall "https://catchall-mc.fastmcp.app/mcp?apiKey=YOUR_CATCHALL_API_KEY"
```

### Option 2: Settings File

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "catchall": {
      "type": "url",
      "url": "https://catchall-mc.fastmcp.app/mcp?apiKey=YOUR_CATCHALL_API_KEY"
    }
  }
}
```

---

## Claude Desktop

Edit your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "catchall": {
      "type": "url",
      "url": "https://catchall-mc.fastmcp.app/mcp?apiKey=YOUR_CATCHALL_API_KEY"
    }
  }
}
```

Restart Claude Desktop after saving.

---

## Claude Web (claude.ai)

Claude Web does not support custom headers for MCP connections, so the API key must be included in the URL.

1. Go to [claude.ai](https://claude.ai)
2. Open **Settings** > **Integrations** or look for the MCP connector option
3. Add a new MCP server with URL:

```
https://catchall-mc.fastmcp.app/mcp?apiKey=YOUR_CATCHALL_API_KEY
```

---

## ChatGPT (Custom GPT)

ChatGPT uses Actions to connect to external APIs. You can create a Custom GPT with the CatchAll API.

### Option 1: Use the MCP-to-OpenAPI Bridge

If the MCP server exposes an OpenAPI schema:

1. Go to [chat.openai.com](https://chat.openai.com) and create a new GPT
2. In the **Configure** tab, go to **Actions**
3. Import the OpenAPI schema from the MCP server
4. Add authentication with your API key

### Option 2: Direct API Integration

Create a Custom GPT with these Actions pointing to the CatchAll API:

**Server URL:** `https://catchall.newscatcherapi.com`

**Authentication:** API Key in header `x-api-key`

**Available Endpoints:**
- `POST /catchAll/submit` - Submit a search query
- `GET /catchAll/status/{job_id}` - Check job status
- `GET /catchAll/pull/{job_id}` - Get results
- `GET /catchAll/jobs/user` - List your jobs
- `POST /catchAll/continue` - Continue a job

See the [API documentation](https://www.newscatcherapi.com/docs/v3/catch-all/overview/introduction) for the full OpenAPI schema.

---

## Available Tools

Once connected, you'll have access to these tools:

| Tool | Description |
|------|-------------|
| `submit_query` | Submit a natural language news search query |
| `get_job_status` | Check if processing is complete |
| `pull_results` | Retrieve clustered articles and summaries |
| `list_user_jobs` | View previous searches |
| `continue_job` | Resume a job needing more data |

## Example Prompts

After connecting, try these prompts:

- "Find recent news about AI startup funding rounds"
- "What M&A deals happened in the tech sector last week?"
- "Search for news about electric vehicles in Europe"
- "Find articles about central bank interest rate decisions"

## Troubleshooting

**Connection failed:**
- Verify your API key is correct
- Check that the URL includes your API key as `?apiKey=YOUR_KEY` (no headers supported in Claude Web/Desktop)
- Ensure you have network access to `catchall-mc.fastmcp.app`

**No results returned:**
- Try broadening your search query
- Extend the time range (e.g., "last 30 days" instead of "last 7 days")
- Check job status - processing can take 30-120 seconds

## Support

- **API Documentation:** [newscatcherapi.com/docs](https://www.newscatcherapi.com/docs/v3/catch-all/overview/introduction)
- **MCP Server Source:** [github.com/Newscatcher/newscatcher-catchall-mcp](https://github.com/Newscatcher/newscatcher-catchall-mcp)
