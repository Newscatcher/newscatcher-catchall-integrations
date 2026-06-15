# Changelog

All notable changes to this repository are documented here.

---

## [2026-06-15]

### Skills — folder renames (all use-case skills now have `-catchall` suffix)
- `competitor-snapshot` → `competitor-snapshot-catchall`
- `fundraising` → `fundraising-catchall`
- `mergers-and-acquisitions` → `m&a-catchall`
- `vc-pack` → `vc-pack-catchall`
- Updated all skill `name:` frontmatter fields to match

### Skills — all updated to latest tested versions
- **Competitor Snapshot** — major `SKILL.md` rewrite; new reference docs: `CONCURRENCY.md`, `JOB-LIFECYCLE.md`, `NEXT-STEPS.md`, `OUTPUT-REPORT.md`, `QUERY-REVIEW.md`; updated `COMPANY-WATCHLIST.md`
- **Fundraising** — updated `SKILL.md`, enhanced `JOB-LIFECYCLE.md`, new `OUTPUT-LIST.md` and `QUERY-REVIEW.md`, added `scripts/build_downloads.py`
- **Mergers & Acquisitions** — same updates as Fundraising
- **VC Pack** — major `SKILL.md` overhaul, new `CONCURRENCY.md`, enhanced `JOB-LIFECYCLE.md`, new `QUERY-REVIEW.md`, added `scripts/render.py`

---

## [2026-06-08]

### Claude Agent — `claude_agent_skill_example.py` major refactor
- **`SKILL_PATH` fixed** — was pointing to `Claude/CatchAll-SKILL/SKILL.md`; now correctly resolves to `skills/general-use-case/SKILL.md`
- **`parse_skill_to_tools()` removed** — replaced with a hardcoded `TOOLS` list covering all 11 jobs + monitor tools with proper JSON Schemas; eliminates a dynamic parsing step that silently produced wrong schemas
- **Monitor endpoint fixed** — `POST /catchAll/monitors/create` → `POST /catchAll/monitors`
- **`update_monitor` cleaned up** — inline webhook removed from request body; now passes `limit` only
- **Model default updated** — `claude-sonnet-4-20250514` → `claude-sonnet-4-5`
- **Error handling** — bare `except:` replaced with `except ValueError` / `except Exception` throughout
- **Windows compatibility** — UTF-8 stdout reconfiguration added so status emojis render correctly on cp1252 consoles
- `system=skill_content` preserved in `run_agent()` — the core differentiator from the non-skill variant
- `README.md` updated with corrected setup instructions and usage examples

---

## [2026-06-05]

### Skills — `general-use-case`
- Applied skill-creator (Anthropic public skill) analysis to `skills/general-use-case/SKILL.md`
- **Description rewrite** — added concrete trigger phrases, made triggering assertive to prevent under-triggering; changed "prefer a dedicated skill" passive language to "when in doubt, use this skill"
- **CRITICAL rule** — added explanation of *why* journalism-style queries fail (intent classifier confusion, not just a style preference)
- **`ed_score_min`** — documented entity confidence threshold parameter for watchlist mode with recommended values and when to lower it
- **Full automation workflow** — new section with the complete 5-step sequence for "alert me weekly when X happens" requests (job → review → webhook → monitor → confirm); covers common trigger phrases like Slack alerts, weekly digests, competitor funding alerts
- **Monitor debugging** — added edge case for "monitor returned 0 results after previously returning N"; guides agent to `get_monitor_status` and reference job re-evaluation

### New skill — VC Pack (`skills/vc-pack-catchall/`)
- Combines funding rounds and M&A acquisitions into a single market-intelligence dashboard
- Runs two parallel CatchAll jobs (funding feed + M&A feed) and joins results at the presentation layer
- Dashboard never renders partial — both feeds must complete before the HTML report is generated
- Covers any market, geography, and timeframe up to 30 days
- Included assets: `assets/dashboard.html` (output template), `assets/render.py` (rendering script)
- Reference docs included: `EXTRACTION.md`, `JOB-LIFECYCLE.md`, `NEXT-STEPS.md`

### Skills — Fundraising and Mergers & Acquisitions (reference docs expanded)
- Added `JOB-LIFECYCLE.md`, `NEXT-STEPS.md`, and `OUTPUT-ARTIFACTS.md` to both skills
- Minor copy fixes to frontmatter trigger phrases in both `SKILL.md` files

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
