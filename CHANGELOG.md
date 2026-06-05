# Changelog

All notable changes to this repository are documented here.

---

## [Unreleased] — 2026-06-05

### Skills — `general-use-case`
- Applied skill-creator (Anthropic public skill) analysis to `skills/general-use-case/SKILL.md`
- **Description rewrite** — added concrete trigger phrases, made triggering assertive to prevent under-triggering; changed "prefer a dedicated skill" passive language to "when in doubt, use this skill"
- **CRITICAL rule** — added explanation of *why* journalism-style queries fail (intent classifier confusion, not just a style preference)
- **`ed_score_min`** — documented entity confidence threshold parameter for watchlist mode with recommended values and when to lower it
- **Full automation workflow** — new section with the complete 5-step sequence for "alert me weekly when X happens" requests (job → review → webhook → monitor → confirm); covers common trigger phrases like Slack alerts, weekly digests, competitor funding alerts
- **Monitor debugging** — added edge case for "monitor returned 0 results after previously returning N"; guides agent to `get_monitor_status` and reference job re-evaluation

---

## [2026-06-04]

### Skills — `general-use-case` (complete rewrite)
- Rewrote `skills/general-use-case/SKILL.md` from API-based to MCP-based
- Removed all HTTP endpoint documentation (MCP handles routing and authentication)
- Removed `assets/` folder references (`example-submit.json`, `example_pull_response.json`) — redundant with MCP tool descriptions
- Removed `references/ENRICHMENT-TYPES.md` and `references/openapi-spec.json` references — redundant with MCP
- Kept `references/VALIDATORS.md` and `references/MONITOR-SCHEDULING.md` — still add genuine value
- **New: `validate_query`** — documented as pre-submission quality check with `good`/`needs_work`/`critical` statuses
- **New: Tool reference** — expanded tool table covering all 7 categories (Jobs, Monitors, Webhooks, Datasets & Entities, Projects, Utilities)
- **New: Job modes** — `base` vs `lite`, when to use each
- **New: Limit vs. page_size** — explicit cost distinction table
- **New: Datasets & Entities** — watchlist mode end-to-end workflow, when to use vs. topic queries, dataset health
- **New: Webhooks** — setup workflow, delivery modes (`full` vs `per_record`), types (generic/slack/teams), auth options
- **New: Projects** — organizational workflow, when to use, safe deletion behavior

### README.md
- Updated `general-use-case` Interface column from `API` to `MCP`
- Updated `general-use-case` use case description to include webhooks, datasets, entities, projects
- Updated General Use Case description section to reference MCP URL

---

## [2026-06-03]

### Repository restructure
- Moved `Claude/CatchAll-SKILL/` content to new `skills/` top-level folder
- Renamed `basic-functionality` folder to `general-use-case`
- Fixed typo in `crew_ai/risk_management_agent/` folder name (was `risk_managment_agent`)

### New skills added
- `skills/competitor-snapshot/` — competitive intelligence skill (MCP + API fallback)
- `skills/fundraising/` — funding announcement tracking skill (MCP)
- `skills/mergers-and-acquisitions/` — M&A deal tracking skill (MCP)

### Skill name convention
- Updated all skill `name:` frontmatter fields to `<use-case>-catchall` suffix pattern:
  - `general-use-case-catchall`
  - `competitor-snapshot-catchall`
  - `fundraising-catchall`
  - `mergers-and-acquisitions-catchall`

### GitHub Actions
- Deleted `.github/workflows/repackage-skill.yml` — workflow watched `Claude/CatchAll-SKILL/**` and auto-packaged a `.zip`; both the trigger path and the artifact are now obsolete

### README.md (complete rewrite)
- Added **"Accessing CatchAll"** section with table of both interfaces (REST API + MCP Server), their URLs, docs links, and relationship explanation
- Added dedicated **"Skills"** section with table (Skill / Use Case / Trigger Phrases / Interface / Folder) and full description for each skill
- Renamed **"Integrations"** section to be framework-only (Claude Agent, Deep Search Agent, Risk Management Agent)
- Updated repository structure diagram to reflect new `skills/` folder layout
- Split Contributing section into separate guidance for skills vs. framework integrations
- Fixed bare URL (`platform.newscatcherapi.com` → `https://platform.newscatcherapi.com`)
- Added MCP docs link: `https://www.newscatcherapi.com/docs/web-search-api/integrations/mcp`
- Added API docs link: `https://www.newscatcherapi.com/docs/web-search-api/get-started/introduction`
- Added Interface annotation to each skill description (`Folder: ... · Interface: MCP (url)`)
