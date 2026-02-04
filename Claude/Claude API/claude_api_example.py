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
            "for the first time - results stream in gradually as processing continues."
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


# Simple example without agent loop
if __name__ == "__main__":
    # Check for required environment variables
    if not CATCHALL_API_KEY:
        print("Error: Please set CATCHALL_API_KEY environment variable")
        print("  export CATCHALL_API_KEY='your_api_key'")
        exit(1)

    # Step 1: Submit a query
    query = "Find recent news about AI startup funding rounds in the last 7 days"
    print(f"\n{'='*60}")
    print(f"Submitting query: {query}")
    print('='*60)

    submit_response = call_catchall_api(
        method="POST",
        path="/catchAll/submit",
        json_data={"query": query, "limit": 10}
    )
    job_id = submit_response["job_id"]
    print(f"Job submitted! Job ID: {job_id}")

    # Step 2: Wait 30 seconds before first pull
    print("\nWaiting 30 seconds before first pull...")
    time.sleep(30)

    # Step 3: Poll for results every 1 minute until job is completed
    while True:
        # Pull current results (streaming - returns partial data)
        print(f"\n{'='*60}")
        print("Pulling results...")
        pull_response = call_catchall_api(
            method="GET",
            path=f"/catchAll/pull/{job_id}",
            params={"page": 1, "page_size": 100}
        )

        status = pull_response.get("status", "unknown")
        clusters = pull_response.get("clusters", [])

        print(f"Status: {status}")
        print(f"Clusters available: {len(clusters)}")

        # Show snapshot of current data
        if clusters:
            print("\n--- Current Results Snapshot ---")
            for i, cluster in enumerate(clusters[:3]):  # Show first 3 clusters
                title = cluster.get("cluster_title", "No title")
                article_count = len(cluster.get("articles", []))
                print(f"  {i+1}. {title} ({article_count} articles)")
            if len(clusters) > 3:
                print(f"  ... and {len(clusters) - 3} more clusters")
            print("--- End Snapshot ---")

        # Check if job is completed
        if status == "completed":
            print(f"\n{'='*60}")
            print("JOB COMPLETED!")
            print('='*60)
            print(f"\nFinal results: {len(clusters)} clusters")

            # Show all final results
            print("\n--- Final Results ---")
            for i, cluster in enumerate(clusters):
                title = cluster.get("cluster_title", "No title")
                summary = cluster.get("summary", "No summary")
                article_count = len(cluster.get("articles", []))
                print(f"\n{i+1}. {title}")
                print(f"   Articles: {article_count}")
                print(f"   Summary: {summary[:200]}..." if len(summary) > 200 else f"   Summary: {summary}")
            print("\n--- End Final Results ---")
            break

        # Job not done yet - wait 1 minute before next poll
        print("\nJob still processing. Waiting 1 minute before next poll...")
        time.sleep(60)
