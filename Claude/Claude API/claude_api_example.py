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

import anthropic
import httpx

# Configuration
CATCHALL_API_KEY = os.environ.get("CATCHALL_API_KEY")
CATCHALL_BASE_URL = "https://catchall.newscatcherapi.com"

# Initialize Anthropic client
client = anthropic.Anthropic()

# Define tools for Claude
TOOLS = [
    {
        "name": "submit_query",
        "description": (
            "Submit a natural language query to search for news articles. "
            "The system will fetch, validate, cluster, and summarize relevant articles. "
            "Returns a job_id that you'll use to check status and retrieve results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g., 'Find all M&A deals in tech sector last 7 days')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_job_status",
        "description": (
            "Check the status of a submitted job. "
            "Status progression: submitted -> analyzing -> fetching -> clustering -> enriching -> completed. "
            "Keep polling until status is 'completed' before pulling results."
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
        "name": "pull_results",
        "description": (
            "Retrieve the results of a completed job. "
            "Only call this after get_job_status shows the job is 'completed'. "
            "Returns clustered and summarized news articles."
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
            result = call_catchall_api(
                method="POST",
                path="/catchAll/submit",
                json_data={"query": tool_input["query"]}
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

    Args:
        user_message: The user's request
        model: Claude model to use

    Returns:
        Claude's final text response
    """
    messages = [{"role": "user", "content": user_message}]

    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print('='*60)

    while True:
        response = client.messages.create(
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

                    # Execute the tool
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

    if not os.environ.get("ANTHROPIC_API_KEY"):
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
    run_agent(example_queries[0])
