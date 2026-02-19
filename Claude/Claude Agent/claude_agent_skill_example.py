"""
Newscatcher CatchAll API with Claude API - SKILL.md Native Integration

This version GENERATES tools from SKILL.md automatically.
NO hardcoded tool definitions - everything comes from SKILL.md!
"""

import json
import os
import time
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

import anthropic
import httpx

# Configuration
CATCHALL_BASE_URL = "https://catchall.newscatcherapi.com"
CATCHALL_API_KEY = os.environ.get("CATCHALL_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# Find SKILL.md
SCRIPT_DIR = Path(__file__).parent
SKILL_PATH = SCRIPT_DIR / ".." / "CatchAll-SKILL" / "SKILL.md"

# Initialize client
client = None

def get_client():
    global client
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return client

def load_skill() -> str:
    """Load SKILL.md content."""
    if SKILL_PATH.exists():
        return SKILL_PATH.read_text()
    else:
        raise FileNotFoundError(f"SKILL.md not found at {SKILL_PATH}")

def parse_skill_to_tools(skill_content: str) -> List[Dict[str, Any]]:
    """
    Parse SKILL.md and automatically generate TOOLS.

    This is the KEY function - it extracts tool definitions from SKILL.md
    so we don't need hardcoded TOOLS!
    """
    tools = []

    # Check what parameters are documented in SKILL
    has_context = "context" in skill_content.lower()
    has_limit = "limit" in skill_content.lower()
    has_dates = "start_date" in skill_content.lower() and "end_date" in skill_content.lower()
    has_validators = "validators" in skill_content.lower()
    has_enrichments = "enrichments" in skill_content.lower()

    # Generate submit_query tool from SKILL.md
    submit_properties = {
        "query": {
            "type": "string",
            "description": "Natural language query (extracted from SKILL.md)"
        }
    }

    if has_context:
        submit_properties["context"] = {
            "type": "string",
            "description": "Additional context to guide extraction"
        }

    if has_limit:
        submit_properties["limit"] = {
            "type": "integer",
            "description": "Maximum number of results. Default is 10 (from SKILL.md)."
        }

    if has_dates:
        submit_properties["start_date"] = {
            "type": "string",
            "description": "Start date in ISO 8601 format"
        }
        submit_properties["end_date"] = {
            "type": "string",
            "description": "End date in ISO 8601 format"
        }

    if has_validators:
        submit_properties["validators"] = {
            "type": "array",
            "description": "Array of validator objects (from SKILL.md)",
            "items": {"type": "object"}
        }

    if has_enrichments:
        submit_properties["enrichments"] = {
            "type": "array",
            "description": "Array of enrichment objects (from SKILL.md)",
            "items": {"type": "object"}
        }

    tools.append({
        "name": "submit_query",
        "description": "Submit query (generated from SKILL.md). See SKILL.md for full docs.",
        "input_schema": {
            "type": "object",
            "properties": submit_properties,
            "required": ["query"]
        }
    })

    # Generate other tools
    tools.append({
        "name": "pull_results",
        "description": "Retrieve results (generated from SKILL.md)",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID"},
                "page": {"type": "integer", "default": 1},
                "page_size": {"type": "integer", "default": 100}
            },
            "required": ["job_id"]
        }
    })

    tools.append({
        "name": "get_job_status",
        "description": "Check job status (generated from SKILL.md)",
        "input_schema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"]
        }
    })

    # Check if continue_job is documented in SKILL
    if "continue" in skill_content.lower() and "new_limit" in skill_content.lower():
        tools.append({
            "name": "continue_job",
            "description": "Continue job with new limit (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"},
                    "new_limit": {"type": "integer"}
                },
                "required": ["job_id", "new_limit"]
            }
        })

    tools.append({
        "name": "list_user_jobs",
        "description": "List all jobs (generated from SKILL.md)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })

    # MONITORS - extracted from SKILL.md
    if "monitors" in skill_content.lower():
        tools.append({
            "name": "create_monitor",
            "description": "Create a recurring monitor from a job (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reference_job_id": {"type": "string", "description": "Job ID to monitor"},
                    "schedule": {"type": "string", "description": "Schedule (e.g., 'every day at 9 AM EST')"},
                    "webhook": {
                        "type": "object",
                        "description": "Optional webhook configuration",
                        "properties": {
                            "url": {"type": "string"},
                            "method": {"type": "string"},
                            "headers": {"type": "object"}
                        }
                    }
                },
                "required": ["reference_job_id", "schedule"]
            }
        })

        tools.append({
            "name": "list_monitors",
            "description": "List all monitors (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        })

        tools.append({
            "name": "pull_monitor_results",
            "description": "Get latest monitor results (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monitor_id": {"type": "string", "description": "Monitor ID"}
                },
                "required": ["monitor_id"]
            }
        })

        tools.append({
            "name": "enable_monitor",
            "description": "Enable a monitor (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monitor_id": {"type": "string", "description": "Monitor ID"}
                },
                "required": ["monitor_id"]
            }
        })

        tools.append({
            "name": "disable_monitor",
            "description": "Disable a monitor (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monitor_id": {"type": "string", "description": "Monitor ID"}
                },
                "required": ["monitor_id"]
            }
        })

        tools.append({
            "name": "update_monitor",
            "description": "Update monitor webhook (generated from SKILL.md)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "monitor_id": {"type": "string", "description": "Monitor ID"},
                    "webhook": {"type": "object", "description": "New webhook config"}
                },
                "required": ["monitor_id", "webhook"]
            }
        })

    return tools

def call_catchall_api(
    method: str,
    path: str,
    json_data: Optional[dict] = None,
    params: Optional[dict] = None
) -> dict:
    """Make request to CatchAll API."""
    if not CATCHALL_API_KEY:
        raise ValueError("CATCHALL_API_KEY not set")

    headers = {
        "x-api-key": CATCHALL_API_KEY,
        "Content-Type": "application/json"
    }

    print(f"\n📡 HTTP {method} {CATCHALL_BASE_URL}{path}")

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
            except:
                error_msg = response.text or f"HTTP {response.status_code}"
            raise ValueError(f"API Error ({response.status_code}): {error_msg}")

        return response.json()

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a CatchAll tool."""
    try:
        if tool_name == "submit_query":
            json_data = {"query": tool_input["query"]}

            # Pass ALL optional parameters
            for key in ["context", "limit", "start_date", "end_date", "validators", "enrichments"]:
                if key in tool_input and tool_input[key] is not None:
                    json_data[key] = tool_input[key]

            if "limit" not in json_data:
                json_data["limit"] = 10

            result = call_catchall_api("POST", "/catchAll/submit", json_data=json_data)

        elif tool_name == "get_job_status":
            result = call_catchall_api("GET", f"/catchAll/status/{tool_input['job_id']}")

        elif tool_name == "pull_results":
            result = call_catchall_api(
                "GET",
                f"/catchAll/pull/{tool_input['job_id']}",
                params={"page": tool_input.get("page", 1), "page_size": tool_input.get("page_size", 100)}
            )

        elif tool_name == "continue_job":
            # new_limit is required (specified in TOOLS)
            json_data = {
                "job_id": tool_input["job_id"],
                "new_limit": tool_input["new_limit"]  # Always present, required by schema
            }
            result = call_catchall_api("POST", "/catchAll/continue", json_data=json_data)

        elif tool_name == "list_user_jobs":
            result = call_catchall_api("GET", "/catchAll/jobs/user")

        # MONITORS
        elif tool_name == "create_monitor":
            json_data = {
                "reference_job_id": tool_input["reference_job_id"],
                "schedule": tool_input["schedule"]
            }
            if "webhook" in tool_input:
                json_data["webhook"] = tool_input["webhook"]
            result = call_catchall_api("POST", "/catchAll/monitors/create", json_data=json_data)

        elif tool_name == "list_monitors":
            result = call_catchall_api("GET", "/catchAll/monitors/")

        elif tool_name == "pull_monitor_results":
            result = call_catchall_api("GET", f"/catchAll/monitors/pull/{tool_input['monitor_id']}")

        elif tool_name == "enable_monitor":
            result = call_catchall_api("POST", f"/catchAll/monitors/{tool_input['monitor_id']}/enable")

        elif tool_name == "disable_monitor":
            result = call_catchall_api("POST", f"/catchAll/monitors/{tool_input['monitor_id']}/disable")

        elif tool_name == "update_monitor":
            result = call_catchall_api(
                "PATCH",
                f"/catchAll/monitors/{tool_input['monitor_id']}",
                json_data={"webhook": tool_input["webhook"]}
            )

        else:
            return f"Error: Unknown tool '{tool_name}'"

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error: {str(e)}"

def run_agent(user_message: str, model: str = "claude-sonnet-4-20250514") -> str:
    """
    Run agent with TOOLS GENERATED FROM SKILL.md!
    """
    # Load SKILL.md
    skill_content = load_skill()
    print("✅ Loaded SKILL.md")

    # GENERATE TOOLS FROM SKILL.md (not hardcoded!)
    tools = parse_skill_to_tools(skill_content)
    print(f"✅ Generated {len(tools)} tools from SKILL.md")
    for tool in tools:
        params_count = len(tool["input_schema"]["properties"])
        print(f"   - {tool['name']} ({params_count} parameters)")

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
            tools=tools,  # ← GENERATED from SKILL.md!
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n🔧 Tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)[:200]}...")

                    if tool_name == "submit_query":
                        result = execute_tool(tool_name, tool_input)
                        try:
                            result_data = json.loads(result)
                            if "job_id" in result_data:
                                job_submitted_time = time.time()
                                print(f"   ⏳ Job submitted")
                        except:
                            pass

                    elif tool_name == "pull_results":
                        if job_submitted_time:
                            elapsed = time.time() - job_submitted_time
                            if elapsed < 30:
                                wait_time = 30 - elapsed
                                print(f"   ⏳ Waiting {wait_time:.0f}s...")
                                time.sleep(wait_time)
                            job_submitted_time = None

                        poll_count = 0
                        while poll_count < 15:
                            poll_count += 1
                            if poll_count > 1:
                                print(f"\n   🔄 Poll #{poll_count}...")

                            result = execute_tool(tool_name, tool_input)

                            try:
                                result_data = json.loads(result)
                                status = result_data.get("status", "")
                                records_count = len(result_data.get("all_records", []))

                                if "completed" in status.lower():
                                    print(f"   ✅ Job completed: {records_count} records")
                                    break
                                else:
                                    # Better UX messaging
                                    if records_count == 0:
                                        # No data yet - job still processing
                                        if "not data found" in status.lower() or "please check later" in status.lower():
                                            print(f"   ⏳ Job still processing, no data yet (status: {status})")
                                        else:
                                            print(f"   ⏳ Processing... Status: {status}")
                                    else:
                                        # Partial results available
                                        print(f"   📊 Partial results: {records_count} records (status: {status})")

                                    if poll_count < 15:
                                        print(f"   ⏰ Waiting 60 seconds before next check...")
                                        time.sleep(60)
                            except:
                                break
                    else:
                        result = execute_tool(tool_name, tool_input)

                    result_str = result if isinstance(result, str) else str(result)
                    preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
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
    if not CATCHALL_API_KEY or not ANTHROPIC_API_KEY:
        print("Error: Set CATCHALL_API_KEY and ANTHROPIC_API_KEY")
        exit(1)

    run_agent("Find electric vehicle news in Europe, limit 15")