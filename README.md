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

Installable skills for the [CatchAll Web Search API](https://www.newscatcherapi.com/docs/web-search-api/get-started/introduction).
Each top-level folder is one skill: drop it into an agent's skills directory
(Claude Code: `.claude/skills/`) or upload it as a zip (claude.ai), with the
CatchAll MCP connected.

## General Use Case Skill
| Skill | What it does                                                                                                                                                              |
|---|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **general-use-case** | General-purpose CatchAll access: submit queries, poll jobs, pull results, monitors, webhooks, datasets, entities, projects. Basic rules on how to effiently use CatchAll. |                                                                                                                  |

## CatchAll Demo Skills

### Single-search

| Skill | What it does |
|---|---|
| **fundraising** | Confirmed startup funding announcements — any stage, geography, vertical. One search → event table + xlsx/JSON/CSV downloads. |
| **mergers-and-acquisitions** | Confirmed M&A events — acquisitions, mergers, asset purchases, acqui-hires. One search → event table + downloads. |

### Deep research (multiple parallel searches)

| Skill | What it does |
|---|---|
| **vc-pack** | A market's funding **and** M&A activity in one view — two parallel searches joined into an interactive dashboard, plus the full dataset as downloads. |
| **competitor-snapshot** | What a company — or a watchlist of up to 100 — has been doing across 7 categories (product, pricing, leadership, customer wins, partnerships, M&A, financial signals). Multi-search sectioned report + downloads. |
| **portfolio-monitoring** | What's changed across a watchlist of up to 100 portfolio companies — capital & exits, distress & risk, leadership & governance, commercial momentum — led by an **Early Warnings** table (companies showing downside signals) and **Events worth watching**. Multi-search sectioned report + downloads. |

### One system, shared references

Skills are composed from a shared reference set: each skill carries the
docs for the concerns it has, and matching files are **byte-identical
copies stamped from one master set** — an edit lands once, upstream, and
every skill picks it up on the next publish.

| Layer | Concern — files | fundraising | mergers-and-acquisitions | vc-pack | competitor-snapshot | portfolio-monitoring |
|---|---|---|---|---|---|---|
| **CORE** — every skill | Lifecycle + intake + footer — `JOB-LIFECYCLE.md` · `QUERY-REVIEW.md` · `NEXT-STEPS.md` · `links.json` | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| **Add-on** | Single-search output — `OUTPUT-LIST.md` · `build_downloads.py` | :white_check_mark: | :white_check_mark: | — | — | — |
| **Add-on** | Sectioned-report output — `OUTPUT-REPORT.md` · `build_report.py` · `catchall_api.py` | — | — | — | :white_check_mark: | :white_check_mark: |
| **Add-on** | Parallel searches — `CONCURRENCY.md` | — | — | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| **Add-on** | Company watchlist — `COMPANY-WATCHLIST.md` | — | — | — | :white_check_mark: | :white_check_mark: |
| **Private** | Skill-specific files | — | — | `scripts/render.py` `assets/dashboard.html` | — | — |

### Inside a skill folder

| Path | What it is |
|---|---|
| `SKILL.md` | The skill itself — triggers, query construction, validators, enrichments, output columns/sections. |
| `references/` | Reference docs the skill reads at run time: job lifecycle & polling, intake questions, the output contract, footer links. Shared concerns are identical across skills — each copy is stamped from one master set. |
| `scripts/` | Code the skill runs — e.g. building the xlsx/JSON/CSV downloads, or vc-pack's dashboard renderer. |
| `assets/` | Static templates the output uses — e.g. vc-pack's dashboard HTML. |

### How this repo is maintained

This repo is **generated**: skills are authored and tested in a private
workbench and mirrored here by a publish script. **Don't edit files here** —
the next publish overwrites them. To request a change or a new skill, open an
issue in this repo.


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
