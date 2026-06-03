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

## Skills

Skills are SKILL.md files that give Claude or any other Agent a specialized, task-specific capability on top of the CatchAll API or CatchAll MCP. Each skill knows how to write the right query, which validators to apply, and how to format the output for its specific use case.

To install a skill with Claude, copy its folder into your project's `.claude/skills/` directory or point Claude at it directly. Same goes with other Agents. You might require to create a .zip file reuniting multiple skill related files together.

### Available Skills

| Skill | Use Case | Trigger Phrases | Folder |
|---|---|---|---|
| General Use Case | General-purpose CatchAll access: submit queries, poll jobs, pull results, set up monitors | Any CatchAll API task without a dedicated skill | [`skills/general-use-case`](./skills/general-use-case/) |
| Competitor Snapshot | Structured digest of a competitor's recent moves: product launches, pricing, leadership, M&A, partnerships | "Snapshot [company]", "what's [competitor] been up to", "competitive brief on [company]" | [`skills/competitor-snapshot`](./skills/competitor-snapshot/) |
| Fundraising | Confirmed funding announcements across any geography, stage, and industry | "Series B raises in Austin last 30 days", "AI startups that raised seed this month" | [`skills/fundraising`](./skills/fundraising/) |
| Mergers & Acquisitions | Confirmed M&A deals — acquisitions, mergers, asset purchases, acqui-hires | "AI companies acquired in the US last 30 days", "fintech mergers this week" | [`skills/mergers-and-acquisitions`](./skills/mergers-and-acquisitions/) |

> **For any contributor:** add a row to the table above each time a new skill is merged. Fill in all four columns. Keep the folder path relative so links stay valid after cloning.

---

## Skill Descriptions

### General Use Case
**Folder:** `skills/general-use-case`

The foundational CatchAll skill. Gives Agnets the full API surface: submit queries with optional validators and enrichments, poll job status, pull structured and clustered results, paginate with `/continue`, and set up recurring monitors with webhook delivery.

Use this skill when the user needs comprehensive web data extraction for a use case not covered by a dedicated skill — or when they want direct control over validators, enrichment types, and scheduling.

→ [Read the skill documentation](./skills/general-use-case/SKILL.md)

---

### Competitor Snapshot
**Folder:** `skills/competitor-snapshot`

Produces a structured digest of a competitor's recent moves across the categories that competitive intelligence teams, product strategists, and sales enablement actually use: product launches, pricing changes, leadership moves, customer wins, partnerships, M&A activity, and financial signals.

Works on a single competitor or a watchlist of up to 100 companies uploaded as CSV. Every event is attributed to the highest-scoring matched company and filtered to surface only high-confidence signals.

Best for: CI analysts, product managers, sales enablement, founders doing market scans, board prep, consultants.

→ [Read the skill documentation](./skills/competitor-snapshot/SKILL.md)

---

### Fundraising
**Folder:** `skills/fundraising`

Finds confirmed funding announcements — pre-seed through Series C and beyond — across any geography, funding stage, and industry vertical. Returns structured event records extracted from web sources, not raw article links.

Built for GTM, VC research, recruiting, and market intelligence workflows. Knows how to write event-scoped queries (describing what happened, not what was written about it) and which enrichments to extract: company name, amount raised, funding stage, investor names, country, and industry.

Best for: VCs tracking deal flow, GTM teams building prospect lists, analysts monitoring market activity.

→ [Read the skill documentation](./skills/fundraising/SKILL.md)

---

### Mergers & Acquisitions
**Folder:** `skills/mergers-and-acquisitions`

Finds confirmed M&A deals — acquisitions, mergers, asset purchases, and acqui-hires — across any geography and industry. Returns structured event records with deal type, parties involved, deal value (where disclosed), and deal status.

Like the Fundraising skill, it operates on the event layer: queries describe real-world deals, not journalism about deals. This distinction is enforced at the query-writing stage.

Best for: competitive intelligence, deal sourcing, market monitoring, GTM targeting of recently-acquired companies.

→ [Read the skill documentation](./skills/mergers-and-acquisitions/SKILL.md)

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
│   ├── general-use-case/          # Core CatchAll API skill (submit → poll → pull, monitors)
│   ├── competitor-snapshot/       # Competitive intelligence skill
│   ├── fundraising/               # Funding round tracking skill
│   └── mergers-and-acquisitions/  # M&A deal tracking skill
├── Claude/
│   └── Claude Agent/              # Anthropic Claude API integration
├── crew_ai/
│   ├── deep_search_agent/         # Iterative research agent (CrewAI)
│   └── risk_management_agent/     # Supply chain risk agent (CrewAI)
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
