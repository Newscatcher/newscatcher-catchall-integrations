"""
Newscatcher CatchAll API with Claude API - Direct Integration Example

This example demonstrates how to use the Newscatcher CatchAll API as tools
with the Claude API (Anthropic SDK).

Requirements:
    pip install anthropic httpx

Usage:
    export CATCHALL_API_KEY="your_api_key"
    export ANTHROPIC_API_KEY="your_anthropic_key"
    python claude_api_example.py
"""

import json
import os
import time

import anthropic
import httpx

# Configuration
CATCHALL_BASE_URL = "https://catchall.newscatcherapi.com"
CATCHALL_API_KEY = os.environ.get("CATCHALL_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Initialize Anthropic client
client = None


def get_client():
    """Get or initialize the Anthropic client."""
    global client
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return client


def configure(catchall_api_key: str = None, anthropic_api_key: str = None):
    """
    Configure API keys programmatically.

    Args:
        catchall_api_key: Your CatchAll API key
        anthropic_api_key: Your Anthropic API key
    """
    global CATCHALL_API_KEY, ANTHROPIC_API_KEY, client
    if catchall_api_key:
        CATCHALL_API_KEY = catchall_api_key
    if anthropic_api_key:
        ANTHROPIC_API_KEY = anthropic_api_key
        client = None  # Reset client to use new key


# Define tools for Claude
TOOLS = [
    {
        "name": "submit_query",
        "description": (
            "Submit a natural language query to search for news articles. "
            "The system will fetch, validate, cluster, and summarize relevant articles. "
            "Returns a job_id. After submitting, wait 30 seconds before calling pull_results "
            "for the first time - results stream in gradually as processing continues. "
            "By default, limits results to 10 clusters. Set fetch_all=true only if the user "
            "explicitly asks for ALL results (e.g., 'find all news', 'get everything')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g., 'Find M&A deals in tech sector last 7 days')"
                },
                "fetch_all": {
                    "type": "boolean",
                    "description": "Set to true only if user explicitly requests ALL results. Default is false (limit to 10).",
                    "default": False
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "pull_results",
        "description": (
            "Retrieve results for a job. Supports streaming - wait 30 seconds after submit_query, then call this. "
            "Results appear gradually as processing continues. The response includes 'status' field - "
            "if not 'completed', more results may be available later. Poll every 1 minute to get new results. "
            "When you get results but status is not 'completed', show the user what's available so far "
            "and let them know more results are coming. Returns clustered and summarized news articles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID returned from submit_query"
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for pagination (default: 1)",
                    "default": 1
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of results per page (default: 100, max: 100)",
                    "default": 100
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_job_status",
        "description": (
            "Check the status of a submitted job. "
            "Status progression: submitted -> analyzing -> fetching -> clustering -> enriching -> completed. "
            "Note: With streaming, you don't need to wait for 'completed' - use pull_results directly "
            "to get partial results as they become available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID returned from submit_query"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "list_user_jobs",
        "description": "List all jobs previously submitted. Returns job history with IDs, queries, statuses, and timestamps.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "continue_job",
        "description": "Continue processing a job that needs additional data fetching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job ID to continue processing"
                }
            },
            "required": ["job_id"]
        }
    }
]


def call_catchall_api(
    method: str,
    path: str,
    json_data: dict | None = None,
    params: dict | None = None
) -> dict:
    """Make a request to the CatchAll API."""
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
    """Execute a CatchAll tool and return the result as a string."""
    try:
        if tool_name == "submit_query":
            # If fetch_all is True, don't include limit; otherwise default to 10
            json_data = {"query": tool_input["query"]}
            if not tool_input.get("fetch_all", False):
                json_data["limit"] = 10
            result = call_catchall_api(
                method="POST",
                path="/catchAll/submit",
                json_data=json_data
            )

        elif tool_name == "get_job_status":
            result = call_catchall_api(
                method="GET",
                path=f"/catchAll/status/{tool_input['job_id']}"
            )

        elif tool_name == "pull_results":
            result = call_catchall_api(
                method="GET",
                path=f"/catchAll/pull/{tool_input['job_id']}",
                params={
                    "page": tool_input.get("page", 1),
                    "page_size": tool_input.get("page_size", 100)
                }
            )

        elif tool_name == "list_user_jobs":
            result = call_catchall_api(
                method="GET",
                path="/catchAll/jobs/user"
            )

        elif tool_name == "continue_job":
            result = call_catchall_api(
                method="POST",
                path="/catchAll/continue",
                json_data={"job_id": tool_input["job_id"]}
            )

        else:
            return f"Error: Unknown tool '{tool_name}'"

        return json.dumps(result, indent=2)

    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def run_agent(user_message: str, model: str = "claude-sonnet-4-20250514") -> str:
    """
    Run an agentic loop with Claude using CatchAll tools.

    Handles streaming results from CatchAll API:
    - After submit_query: waits 30 seconds before first pull
    - After pull_results with incomplete status: waits 1 minute before next poll
    - Shows partial results as they become available

    Args:
        user_message: The user's request
        model: Claude model to use

    Returns:
        Claude's final text response
    """
    messages = [{"role": "user", "content": user_message}]
    active_job_id = None
    job_submitted_time = None

    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print('='*60)

    while True:
        response = get_client().messages.create(
            model=model,
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"\n🔧 Tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input)}")

                    # Handle timing for streaming workflow
                    if tool_name == "submit_query":
                        # Execute submit
                        result = execute_tool(tool_name, tool_input)

                        # Track job for timing
                        try:
                            result_data = json.loads(result)
                            if "job_id" in result_data:
                                active_job_id = result_data["job_id"]
                                job_submitted_time = time.time()
                                print(f"   ⏳ Job submitted. Waiting 30 seconds before first pull...")
                        except json.JSONDecodeError:
                            pass

                    elif tool_name == "get_job_status":
                        # Execute status check
                        result = execute_tool(tool_name, tool_input)

                        # Format status nicely for display
                        try:
                            result_data = json.loads(result)
                            steps = result_data.get("steps", [])
                            completed_steps = sum(1 for s in steps if s.get("completed"))
                            total_steps = len(steps) if steps else 7  # Default to 7 if no steps
                            current_status = result_data.get("status", "unknown")
                            print(f"   📊 Progress: {completed_steps}/{total_steps} steps completed")
                            print(f"   📍 Current status: {current_status}")
                        except json.JSONDecodeError:
                            pass

                    elif tool_name == "pull_results":
                        # Ensure minimum 30 seconds after submit before first pull
                        if job_submitted_time is not None:
                            elapsed = time.time() - job_submitted_time
                            if elapsed < 30:
                                wait_time = 30 - elapsed
                                print(f"   ⏳ Waiting {wait_time:.0f} seconds before first pull...")
                                time.sleep(wait_time)
                            job_submitted_time = None  # Only enforce once

                        # Keep polling until job is completed
                        poll_count = 0
                        while True:
                            poll_count += 1
                            if poll_count > 1:
                                print(f"\n   🔄 Poll #{poll_count}...")

                            # Execute pull
                            result = execute_tool(tool_name, tool_input)

                            try:
                                result_data = json.loads(result)
                                status = result_data.get("status", "")
                                clusters_count = len(result_data.get("clusters", []))

                                if "completed" in status.lower():
                                    print(f"   ✅ Job completed with {clusters_count} clusters")
                                    break
                                else:
                                    print(f"   📊 Got {clusters_count} clusters so far (status: {status})")
                                    print(f"   ⏳ Job still processing. Waiting 1 minute before next poll...")
                                    time.sleep(60)
                            except json.JSONDecodeError:
                                # If we can't parse, break to avoid infinite loop
                                break
                    else:
                        # Other tools - execute normally
                        result = execute_tool(tool_name, tool_input)

                    # Show truncated result
                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"   Result: {preview}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add assistant response and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Claude is done - extract and return the final text
            final_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_response += block.text

            print(f"\n{'='*60}")
            print("Assistant:")
            print(final_response)
            print('='*60)

            return final_response


# Example usage
if __name__ == "__main__":
    # Check for required environment variables
    if not CATCHALL_API_KEY:
        print("Error: Please set CATCHALL_API_KEY environment variable")
        print("  export CATCHALL_API_KEY='your_api_key'")
        exit(1)

    if not ANTHROPIC_API_KEY:
        print("Error: Please set ANTHROPIC_API_KEY environment variable")
        print("  export ANTHROPIC_API_KEY='your_api_key'")
        exit(1)

    # Example queries to try:
    example_queries = [
        "Find recent news about AI startup funding rounds in the last 7 days",
        "Search for news about electric vehicle companies in Europe",
        "What are the latest developments in quantum computing?",
    ]

    # Run with the first example
    run_agent(example_queries[1])
