# NewsCatcher CatchAll — Integration Examples

This repository is a collection of ready-to-use integration examples that show how to connect the **NewsCatcher CatchAll API** to popular AI frameworks and tools. Whether you want to wire it into an autonomous agent, use it inside Claude Code, or build a multi-agent pipeline, you will find a working reference here.

---

## What Is CatchAll?

[CatchAll](https://www.newscatcherapi.com/docs/web-search-api/get-started/introduction) is NewsCatcher's Web Search API. It lets you extract structured, validated data from thousands of online sources — news articles, press releases, regulatory filings, and more — at scale. You define what you want to track, and CatchAll fetches, parses, enriches, and delivers it.

Core workflow:

1. **Submit** a query or create a monitor
2. **Poll** until the job is complete
3. **Pull** the structured results
4. **Continue** to page through additional records if needed

---

## Accessing CatchAll

CatchAll exposes two interfaces. Both require an API key from [platform.newscatcherapi.com](https://platform.newscatcherapi.com).

| Interface | URL | Docs | Best for |
|---|---|---|---|
| **REST API** | `https://catchall.newscatcherapi.com` | [API docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/introduction) | Direct integration, full parameter control, framework-based agents |
| **MCP Server** | `https://catchall-mcp.newscatcherapi.com/mcp?apiKey=YOUR_API_KEY` | [MCP docs](https://www.newscatcherapi.com/docs/web-search-api/integrations/mcp) | Agent skills — provides a simplified, tool-oriented interface |

The MCP server calls the REST API under the hood. The API is the source of truth; MCP is a convenience layer that reduces boilerplate for agent skills.

---

## Skills

Skills are SKILL.md files that give Claude or any other Agent a specialized, task-specific capability on top of the CatchAll MCP. Each skill knows how to write the right query, which validators to apply, and how to format the output for its specific use case.

To install a skill with Claude, copy its folder into your project's `.claude/skills/` directory or point Claude at it directly. Same goes with other Agents. You might require to create a .zip file reuniting multiple skill related files together.

### Available Skills

| Skill | Use Case | Trigger Phrases | Interface | Folder |
|---|---|---|---|---|
| General Use Case | General-purpose CatchAll access: submit queries, poll jobs, pull results, monitors, webhooks, datasets, entities, projects | Any CatchAll task without a dedicated skill | MCP | [`skills/general-use-case`](./skills/general-use-case/) |
| Competitor Snapshot | Structured digest of a competitor's recent moves: product launches, pricing, leadership, M&A, partnerships | "Snapshot [company]", "what's [competitor] been up to", "competitive brief on [company]" | MCP| [`skills/competitor-snapshot-catchall`](./skills/competitor-snapshot-catchall/) |
| Fundraising | Confirmed funding announcements across any geography, stage, and industry | "Series B raises in Austin last 30 days", "AI startups that raised seed this month" | MCP | [`skills/fundraising-catchall`](./skills/fundraising-catchall/) |
| Mergers & Acquisitions | Confirmed M&A deals — acquisitions, mergers, asset purchases, acqui-hires | "AI companies acquired in the US last 30 days", "fintech mergers this week" | MCP | [`skills/m&a-catchall`](./skills/m&a-catchall/) |
| VC Pack | Combined funding + M&A market intelligence dashboard — capital flowing into and out of a sector in one view | "VC pack for fintech", "funding and M&A in cybersecurity last 30 days", "capital activity in healthcare AI", "where is money moving in climate" | MCP | [`skills/vc-pack-catchall`](./skills/vc-pack-catchall/) |

> **For any contributor:** add a row to the table above each time a new skill is merged. Fill in all four columns. Keep the folder path relative so links stay valid after cloning.

---

## Skill Descriptions

### General Use Case
**Folder:** `skills/general-use-case` · **Interface:** MCP (`https://catchall-mcp.newscatcherapi.com/mcp`)

The foundational CatchAll skill. Covers the full platform surface via MCP: jobs, monitors, webhooks, datasets, entities, and projects. Use it for any CatchAll task not covered by a dedicated use-case skill — or when the user needs direct control over validators, enrichments, watchlists, or delivery setup.

→ [Read the skill documentation](./skills/general-use-case/SKILL.md)

---

### Competitor Snapshot
**Folder:** `skills/competitor-snapshot-catchall` · **Interface:** MCP (`https://catchall-mcp.newscatcherapi.com/mcp`) — falls back to REST API if MCP is unavailable

Produces a structured digest of a competitor's recent moves across the categories that competitive intelligence teams, product strategists, and sales enablement actually use: product launches, pricing changes, leadership moves, customer wins, partnerships, M&A activity, and financial signals.

Works on a single competitor or a watchlist of up to 100 companies uploaded as CSV. Every event is attributed to the highest-scoring matched company and filtered to surface only high-confidence signals.

Best for: CI analysts, product managers, sales enablement, founders doing market scans, board prep, consultants.

→ [Read the skill documentation](./skills/competitor-snapshot-catchall/SKILL.md)

---

### Fundraising
**Folder:** `skills/fundraising-catchall` · **Interface:** MCP (`https://catchall-mcp.newscatcherapi.com/mcp`)

Finds confirmed funding announcements — pre-seed through Series C and beyond — across any geography, funding stage, and industry vertical. Returns structured event records extracted from web sources, not raw article links.

Built for GTM, VC research, recruiting, and market intelligence workflows. Knows how to write event-scoped queries (describing what happened, not what was written about it) and which enrichments to extract: company name, amount raised, funding stage, investor names, country, and industry.

Best for: VCs tracking deal flow, GTM teams building prospect lists, analysts monitoring market activity.

→ [Read the skill documentation](./skills/fundraising-catchall/SKILL.md)

---

### Mergers & Acquisitions
**Folder:** `skills/m&a-catchall` · **Interface:** MCP (`https://catchall-mcp.newscatcherapi.com/mcp`)

Finds confirmed M&A deals — acquisitions, mergers, asset purchases, and acqui-hires — across any geography and industry. Returns structured event records with deal type, parties involved, deal value (where disclosed), and deal status.

Like the Fundraising skill, it operates on the event layer: queries describe real-world deals, not journalism about deals. This distinction is enforced at the query-writing stage.

Best for: competitive intelligence, deal sourcing, market monitoring, GTM targeting of recently-acquired companies.

→ [Read the skill documentation](./skills/m&a-catchall/SKILL.md)

---

### VC Pack
**Folder:** `skills/vc-pack-catchall` · **Interface:** MCP (`https://catchall-mcp.newscatcherapi.com/mcp`)

Delivers a combined market-intelligence dashboard covering both capital inflows (funding rounds) and outflows (acquisitions) for any sector, geography, and timeframe up to 30 days. Runs two parallel CatchAll jobs — one for funding events, one for M&A deals — and merges the results into a single HTML dashboard.

The dashboard is never shown in a partial state: both feeds must complete before any aggregate statistics (deal-stage breakdown, sub-sectors, capital ratio, top-3 deals, mega-rounds %) are computed. Progress during the run is shown as a live side-by-side status table instead.

Includes `assets/dashboard.html` (visual output template), `assets/render.py` (rendering script), and `scripts/render.py` (standalone render runner).

Best for: VCs and analysts who want a full picture of where capital is moving in a market — not just funding or just M&A in isolation.

→ [Read the skill documentation](./skills/vc-pack-catchall/SKILL.md)

---

## Integrations

Framework-based integrations that embed CatchAll inside an agent or multi-agent pipeline.

### Currently Available

| Name | Framework | Use Case | Folder |
|---|---|---|---|
| Claude Agent | Anthropic Claude API | Autonomous news research via tool calls | [`Claude/Claude Agent`](./Claude/Claude%20Agent/) |
| Deep Search Agent | CrewAI | Iterative news research with report generation | [`crew_ai/deep_search_agent`](./crew_ai/deep_search_agent/) |
| Risk Management Agent | CrewAI | Automotive supply chain risk intelligence | [`crew_ai/risk_management_agent`](./crew_ai/risk_management_agent/) |

> **For any contributor:** add a row to the table above each time a new integration is merged. Fill in all four columns. Keep the folder path relative so links stay valid after cloning.

---

## Integration Descriptions

### Claude Agent
**Folder:** `Claude/Claude Agent`

Wraps the CatchAll API as Claude tool calls. Claude autonomously decides when to submit a query, when to poll for status, and when to pull results — you just provide a prompt. Supports streaming output and configurable result limits.

Best for: ad-hoc research tasks, internal tools, or any situation where you want an LLM to drive the information-gathering loop.

→ [Read the setup guide](./Claude/Claude%20Agent/README.md)

---

### Deep Search Agent (CrewAI)
**Folder:** `crew_ai/deep_search_agent`

A multi-agent pipeline built with CrewAI that runs an iterative search loop: plan → search → evaluate → retry (up to 5 times with refined queries) → synthesize a markdown report. Supports interactive follow-up chat after the report is generated.

Best for: deep research tasks where a single query is not enough and the agent needs to refine its approach.

→ [Read the setup guide](./crew_ai/deep_search_agent/README.md)

---

### Risk Management Agent (CrewAI)
**Folder:** `crew_ai/risk_management_agent`

A specialized CrewAI system for monitoring supply chain risks affecting automotive OEMs in the EU. Three agents collaborate — Intelligence Officer, Risk Analyst, Executive Analyst — to categorize risks across eight dimensions: semiconductor shortages, raw material scarcity, logistics delays, labor disruptions, geopolitical events, supplier financial health, energy crises, and competitive threats.

Best for: domain-specific intelligence workflows where you need structured, categorized output rather than raw search results.

→ [Read the setup guide](./crew_ai/risk_management_agent/README.md)

---

## Getting Started

Each skill and integration is self-contained. Navigate to its folder and follow the README or SKILL.md inside. You will generally need:

- A **NewsCatcher CatchAll API key** — get one on [platform.newscatcherapi.com](https://platform.newscatcherapi.com) if you do not have one yet
- An API key for the LLM provider used by the integration (Anthropic or Google Gemini, depending on the example)
- Python 3.10+ and the dependencies listed in the integration's `requirements.txt` or `pyproject.toml`

---

## Repository Structure

```
newscatcher-catchall-integrations/
├── skills/
│   ├── general-use-case/              # Core CatchAll skill (jobs, monitors, webhooks, datasets)
│   ├── competitor-snapshot-catchall/  # Competitive intelligence skill
│   ├── fundraising-catchall/          # Funding round tracking skill
│   ├── m&a-catchall/                  # M&A deal tracking skill
│   └── vc-pack-catchall/              # Combined funding + M&A market dashboard skill
├── Claude/
│   └── Claude Agent/                  # Anthropic Claude API integration
├── crew_ai/
│   ├── deep_search_agent/             # Iterative research agent (CrewAI)
│   └── risk_management_agent/         # Supply chain risk agent (CrewAI)
└── README.md
```

---

## Contributing

If you are adding a new skill:

1. Create a folder under `skills/` following the naming convention of existing ones
2. Include a `SKILL.md` with the skill's description frontmatter, trigger phrases, query-building rules, and output format
3. Add reference files under `references/` for any domain-specific lookup tables the skill needs
4. Add a row to the **Available Skills** table in this file

If you are adding a new framework integration:

1. Create a new folder following the naming convention of existing ones
2. Include a `README.md` with setup instructions and at least one usage example
3. Add an `env_example` file listing all required environment variables (no real values)
4. Add a row to the **Currently Available** integrations table in this file

Questions? Reach out to the [NewsCatcher team](mailto:support@newscatcherapi.com).
