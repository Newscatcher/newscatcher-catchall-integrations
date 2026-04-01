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

## Integrations

### Currently Available

| Name | Framework | Use Case | Folder |
|---|---|---|---|
| Claude Agent | Anthropic Claude API | Autonomous news research via tool calls | [`Claude/Claude Agent`](./Claude/Claude%20Agent/) |
| CatchAll SKILL | Claude Code | Structured data extraction inside Claude Code | [`Claude/CatchAll-SKILL`](./Claude/CatchAll-SKILL/) |
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

### CatchAll SKILL (Claude Code)
**Folder:** `Claude/CatchAll-SKILL`

A Claude Code SKILL that gives Claude the ability to extract structured data from the web at scale. Supports validators (boolean filters to control data quality), enrichment types (text, number, date, option, URL, company), and recurring monitors with webhook delivery.

Best for: power users of Claude Code who want CatchAll available as a slash-command-style capability.

→ [Read the skill documentation](./Claude/CatchAll-SKILL/SKILL.md)

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

Each integration is self-contained. Navigate to its folder and follow the README inside. You will generally need:

- A **NewsCatcher CatchAll API key** — get one on [platform.newscatcherapi.com](platform.newscatcherapi.com) if you do not have one yet
- An API key for the LLM provider used by the integration (Anthropic or Google Gemini, depending on the example)
- Python 3.10+ and the dependencies listed in the integration's `requirements.txt` or `pyproject.toml`

---

## Repository Structure

```
newscatcher-catchall-integrations/
├── Claude/
│   ├── Claude Agent/          # Anthropic Claude API integration
│   └── CatchAll-SKILL/        # Claude Code SKILL
├── crew_ai/
│   ├── deep_search_agent/     # Iterative research agent
│   └── risk_management_agent/ # Supply chain risk agent
└── README.md
```

---

## Contributing

If you are adding a new integration:

1. Create a new folder following the naming convention of existing ones
2. Include a `README.md` with setup instructions and at least one usage example
3. Add an `env_example` file listing all required environment variables (no real values)
4. Add a row to the **Currently Available** table in this file

Questions? Reach out to the [NewsCatcher team](support@newscatcherapi.com).
