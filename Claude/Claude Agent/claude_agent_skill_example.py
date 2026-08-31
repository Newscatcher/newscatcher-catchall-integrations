"""
Newscatcher CatchAll API with Claude API - Skill-Based Integration

This variant loads the general-use-case CatchAll Skill as Claude's system
prompt. The Skill provides query-writing rules, validator and enrichment
patterns, monitor setup guidance, and output formatting instructions — so
Claude automatically applies best practices without any hardcoded query logic.

The tool definitions cover jobs and monitors against the CatchAll REST API.
For MCP-based usage (recommended for chat interfaces), see the MCP integration
page in the docs.

Requirements:
    pip install anthropic httpx

Usage:
    export CATCHALL_API_KEY="your_api_key"
    export ANTHROPIC_API_KEY="your_anthropic_key"
    python claude_agent_skill_example.py
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic
import httpx

# Emit UTF-8 so the status emojis below don't raise UnicodeEncodeError on
# consoles that default to a non-UTF-8 encoding (e.g. Windows cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Configuration
CATCHALL_BASE_URL = "https://catchall.newscatcherapi.com"
CATCHALL_API_KEY = os.environ.get("CATCHALL_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Path to the general-use-case Skill
SKILL_PATH = (
    Path(__file__).parent / ".." / ".." / "skills" / "general-use-case-catchall" / "SKILL.md"
)

# Initialize Anthropic client
client = None


def get_client():
    """Get or initialize the Anthropic client."""
    global client
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return client


def load_skill() -> str:
    """
    Load the general-use-case Skill file as a system prompt.

    Returns:
        str: Full contents of SKILL.md.

    Raises:
        FileNotFoundError: If SKILL.md is not found at the expected path.
    """
    path = SKILL_PATH.resolve()
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md not found at {path}")
    return path.read_text()


# Tool definitions — jobs and monitors
TOOLS = [
    {
        "name": "submit_query",
        "description": (
            "Submit a natural language query to the CatchAll API and start a job. "
            "Returns a job_id. Write the query as a real-world event description, "
            "not a request for articles. "
            "Status progression: submitted → analyzing → fetching → clustering → enriching → completed. "
            "Poll get_job_status every 60 seconds; pull results once status reaches "
            "'enriching' or 'completed'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language event description. "
                        "Example: 'Series B funding rounds announced by fintech companies in the last 14 days'"
                    )
                },
                "mode": {
                    "type": "string",
                    "enum": ["base", "lite"],
                    "description": (
                        "'base' (default): full validation and enrichment pipeline. "
                        "'lite': faster and lower cost — validators only, no enrichment metadata."
                    )
                },
                "limit": {
                    "type": "integer",
                    "description": (
                        "Maximum number of records to process and validate. "
                        "Affects billing. Omit for exhaustive runs."
                    )
                },
                "start_date": {
                    "type": "string",
                    "description": "Start of date range in ISO 8601 format (e.g., '2026-05-01')"
                },
                "end_date": {
                    "type": "string",
                    "description": "End of date range in ISO 8601 format (e.g., '2026-05-31')"
                },
                "validators": {
                    "type": "array",
                    "description": (
                        "Custom boolean filters. Each item: "
                        "{\"name\": str, \"description\": str, \"type\": \"boolean\"}. "
                        "Leave empty to use auto-selected validators."
                    ),
                    "items": {"type": "object"}
                },
                "enrichments": {
                    "type": "array",
                    "description": (
                        "Fields to extract from each valid record. Each item: "
                        "{\"name\": str, \"description\": str, \"type\": \"text\"|\"number\"|\"date\"|\"option\"|\"url\"|\"company\"}."
                    ),
                    "items": {"type": "object"}
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_job_status",
        "description": (
            "Check the processing status of a submitted job. "
            "Status values: submitted, analyzing, fetching, clustering, enriching, completed, failed. "
            "Poll every 60 seconds until 'completed' or 'failed'. "
            "Results are accessible during 'enriching' but may be incomplete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID returned by submit_query"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "pull_results",
        "description": (
            "Retrieve validated, enriched records for a completed or in-progress job. "
            "Wait at least 60 seconds after submit_query before the first call. "
            "Use page and page_size to paginate through large result sets. "
            "page_size does not affect billing — only limit in submit_query does."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID returned by submit_query"
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 1)",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "Records per page (default: 100, max: 100)",
                    "default": 100
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "continue_job",
        "description": (
            "Expand a completed job to process additional records beyond the original limit. "
            "Use when the user asks for more results after reviewing the initial output."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID to expand"
                },
                "new_limit": {
                    "type": "integer",
                    "description": (
                        "New total record limit. Must be higher than the original limit. "
                        "Omit to use the plan maximum."
                    )
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "list_user_jobs",
        "description": (
            "List jobs submitted by the authenticated user, "
            "sorted by creation date (most recent first)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_monitor",
        "description": (
            "Create a recurring monitor from a completed reference job. "
            "The monitor re-runs the job's query on the given schedule and deduplicates "
            "results across runs. Only use a completed job as the reference."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reference_job_id": {
                    "type": "string",
                    "description": "ID of a completed job whose query and settings this monitor will repeat"
                },
                "schedule": {
                    "type": "string",
                    "description": (
                        "Natural language schedule with timezone. "
                        "Examples: 'every day at 9 AM EST', 'every Monday at 8 AM UTC'"
                    )
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records per monitor run. Defaults to the reference job's limit."
                },
                "backfill": {
                    "type": "boolean",
                    "description": (
                        "Fill the gap between the reference job's end date and now on the first run. "
                        "Default: true. Only effective if the reference job's end date is within the last 7 days."
                    )
                },
                "timezone": {
                    "type": "string",
                    "description": (
                        "IANA timezone used when the schedule string does not specify one "
                        "(e.g., 'America/New_York'). Default: 'UTC'."
                    )
                }
            },
            "required": ["reference_job_id", "schedule"]
        }
    },
    {
        "name": "list_monitors",
        "description": "List all monitors for the authenticated user.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "pull_monitor_results",
        "description": (
            "Retrieve the latest aggregated results from a monitor, "
            "deduplicated across all runs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "monitor_id": {
                    "type": "string",
                    "description": "Monitor ID"
                }
            },
            "required": ["monitor_id"]
        }
    },
    {
        "name": "enable_monitor",
        "description": "Re-enable a previously disabled monitor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monitor_id": {
                    "type": "string",
                    "description": "Monitor ID"
                }
            },
            "required": ["monitor_id"]
        }
    },
    {
        "name": "disable_monitor",
        "description": "Pause a monitor without deleting it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monitor_id": {
                    "type": "string",
                    "description": "Monitor ID"
                }
            },
            "required": ["monitor_id"]
        }
    },
    {
        "name": "update_monitor",
        "description": "Update the per-run record limit for an existing monitor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monitor_id": {
                    "type": "string",
                    "description": "Monitor ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "New maximum records per run"
                }
            },
            "required": ["monitor_id"]
        }
    }
]


def call_catchall_api(
    method: str,
    path: str,
    json_data: dict | None = None,
    params: dict | None = None
) -> dict:
    """
    Make a request to the CatchAll REST API.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE).
        path: API path relative to CATCHALL_BASE_URL.
        json_data: Request body for POST/PATCH requests.
        params: URL query parameters.

    Returns:
        dict: Parsed JSON response.

    Raises:
        ValueError: On API errors (4xx/5xx) or missing API key.
    """
    if not CATCHALL_API_KEY:
        raise ValueError("CATCHALL_API_KEY environment variable is not set")

    headers = {
        "x-api-key": CATCHALL_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    with httpx.Client(base_url=CATCHALL_BASE_URL, timeout=60.0) as http_client:
        response = http_client.request(
            method=method,
            url=path,
            headers=headers,
            json=json_data,
            params=params
        )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(error_data))
            except Exception:
                error_msg = response.text or f"HTTP {response.status_code}"
            raise ValueError(f"API Error ({response.status_code}): {error_msg}")

        return response.json()


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a CatchAll tool and return the result as a JSON string.

    Args:
        tool_name: Name of the tool to execute.
        tool_input: Tool input parameters from Claude.

    Returns:
        str: JSON-encoded API response, or an error message string.
    """
    try:
        if tool_name == "submit_query":
            json_data = {"query": tool_input["query"]}
            for key in ["mode", "limit", "start_date", "end_date", "validators", "enrichments"]:
                if tool_input.get(key) is not None:
                    json_data[key] = tool_input[key]
            result = call_catchall_api("POST", "/catchAll/submit", json_data=json_data)

        elif tool_name == "get_job_status":
            result = call_catchall_api("GET", f"/catchAll/status/{tool_input['job_id']}")

        elif tool_name == "pull_results":
            result = call_catchall_api(
                "GET",
                f"/catchAll/pull/{tool_input['job_id']}",
                params={
                    "page": tool_input.get("page", 1),
                    "page_size": tool_input.get("page_size", 100)
                }
            )

        elif tool_name == "continue_job":
            json_data = {"job_id": tool_input["job_id"]}
            if tool_input.get("new_limit") is not None:
                json_data["new_limit"] = tool_input["new_limit"]
            result = call_catchall_api("POST", "/catchAll/continue", json_data=json_data)

        elif tool_name == "list_user_jobs":
            result = call_catchall_api("GET", "/catchAll/jobs/user")

        elif tool_name == "create_monitor":
            json_data = {
                "reference_job_id": tool_input["reference_job_id"],
                "schedule": tool_input["schedule"]
            }
            for key in ["limit", "backfill", "timezone"]:
                if tool_input.get(key) is not None:
                    json_data[key] = tool_input[key]
            result = call_catchall_api("POST", "/catchAll/monitors", json_data=json_data)

        elif tool_name == "list_monitors":
            result = call_catchall_api("GET", "/catchAll/monitors")

        elif tool_name == "pull_monitor_results":
            result = call_catchall_api(
                "GET", f"/catchAll/monitors/pull/{tool_input['monitor_id']}"
            )

        elif tool_name == "enable_monitor":
            result = call_catchall_api(
                "POST", f"/catchAll/monitors/{tool_input['monitor_id']}/enable"
            )

        elif tool_name == "disable_monitor":
            result = call_catchall_api(
                "POST", f"/catchAll/monitors/{tool_input['monitor_id']}/disable"
            )

        elif tool_name == "update_monitor":
            json_data = {}
            if tool_input.get("limit") is not None:
                json_data["limit"] = tool_input["limit"]
            result = call_catchall_api(
                "PATCH",
                f"/catchAll/monitors/{tool_input['monitor_id']}",
                json_data=json_data
            )

        else:
            return f"Error: Unknown tool '{tool_name}'"

        return json.dumps(result, indent=2)

    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def run_agent(user_message: str, model: str = "claude-sonnet-4-5") -> str:
    """
    Run an agentic loop with Claude using CatchAll tools and the Skill as system prompt.

    The Skill loaded from SKILL.md guides Claude on query construction, validators,
    enrichments, monitor setup, and result presentation — no hardcoded query logic needed.

    Args:
        user_message: The user's research request.
        model: Claude model to use.

    Returns:
        str: Claude's final text response.
    """
    skill_content = load_skill()

    messages = [{"role": "user", "content": user_message}]
    job_submitted_time = None

    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print('='*60)

    while True:
        response = get_client().messages.create(
            model=model,
            max_tokens=4096,
            system=skill_content,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n🔧 Tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input)}")

                    if tool_name == "submit_query":
                        result = execute_tool(tool_name, tool_input)
                        try:
                            result_data = json.loads(result)
                            if "job_id" in result_data:
                                job_submitted_time = time.time()
                                print("   ⏳ Job submitted. Waiting 60 seconds before first pull...")
                        except json.JSONDecodeError:
                            pass

                    elif tool_name == "get_job_status":
                        result = execute_tool(tool_name, tool_input)
                        try:
                            result_data = json.loads(result)
                            steps = result_data.get("steps", [])
                            completed_steps = sum(1 for s in steps if s.get("completed"))
                            total_steps = len(steps) if steps else 6
                            print(f"   📊 Progress: {completed_steps}/{total_steps} steps — {result_data.get('status', 'unknown')}")
                        except json.JSONDecodeError:
                            pass

                    elif tool_name == "pull_results":
                        if job_submitted_time is not None:
                            elapsed = time.time() - job_submitted_time
                            if elapsed < 60:
                                wait_time = 60 - elapsed
                                print(f"   ⏳ Waiting {wait_time:.0f} seconds before first pull...")
                                time.sleep(wait_time)
                            job_submitted_time = None

                        poll_count = 0
                        while True:
                            poll_count += 1
                            if poll_count > 1:
                                print(f"\n   🔄 Poll #{poll_count}...")

                            result = execute_tool(tool_name, tool_input)

                            try:
                                result_data = json.loads(result)
                                status = result_data.get("status", "")
                                records_count = len(result_data.get("all_records", []))

                                if "completed" in status.lower():
                                    print(f"   ✅ Completed — {records_count} records")
                                    break
                                else:
                                    print(f"   📊 {records_count} records so far (status: {status})")
                                    print("   ⏳ Waiting 60 seconds before next poll...")
                                    time.sleep(60)
                            except json.JSONDecodeError:
                                break
                    else:
                        result = execute_tool(tool_name, tool_input)

                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"   Result: {preview}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            final_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_response += block.text

            print(f"\n{'='*60}")
            print("Assistant:")
            print(final_response)
            print('='*60)

            return final_response


if __name__ == "__main__":
    if not CATCHALL_API_KEY:
        print("Error: Please set CATCHALL_API_KEY environment variable")
        print("  export CATCHALL_API_KEY='your_api_key'")
        exit(1)

    if not ANTHROPIC_API_KEY:
        print("Error: Please set ANTHROPIC_API_KEY environment variable")
        print("  export ANTHROPIC_API_KEY='your_api_key'")
        exit(1)

    run_agent("Find electric vehicle funding rounds in Europe in the last 14 days, limit 15")
