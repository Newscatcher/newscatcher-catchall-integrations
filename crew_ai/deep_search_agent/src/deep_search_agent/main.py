#!/usr/bin/env python
"""Deep Search Agent - Iterative news research with follow-up chat."""

import os
import re
import json
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from dotenv import load_dotenv
load_dotenv()

MAX_CONTEXT_CHARS = 400_000


def slugify(text, max_len=50):
    slug = re.sub(r'[^\w\s-]', '', text.lower().strip())
    return re.sub(r'[\s_-]+', '_', slug)[:max_len].rstrip('_')


def build_context(report, results, query):
    """Build chat context from report and raw results."""
    total_records = sum(r.get('valid_records', 0) for r in results)
    
    context = f"""# Research Context
**Query:** {query}
**Records:** {total_records}

# Report
{report}
"""
    
    if not results:
        return context
    
    # Add raw data if space permits
    raw_lines = ["\n# Raw Data\n"]
    used = len(context)
    
    for batch in results:
        for record in batch.get("all_records", []):
            entry = f"\n## {record.get('record_title', 'Untitled')}\n"
            
            enrichment = record.get("enrichment", {})
            if enrichment.get("schema_based_summary"):
                entry += f"{enrichment['schema_based_summary']}\n"
            
            for key in ["affected_manufacturers", "disruption_causes"]:
                if enrichment.get(key):
                    entry += f"- {key}: {enrichment[key]}\n"
            
            citations = record.get("citations", [])[:3]
            if citations:
                entry += "Sources: " + ", ".join(c.get("title", "")[:50] for c in citations) + "\n"
            
            if used + len(entry) > MAX_CONTEXT_CHARS:
                raw_lines.append("\n[Additional records truncated]\n")
                break
            
            raw_lines.append(entry)
            used += len(entry)
    
    return context + "".join(raw_lines)


def chat(report, results, query):
    """Interactive chat about the research."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("Install: pip install google-generativeai")
        return
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Set GEMINI_API_KEY")
        return
    
    genai.configure(api_key=api_key)
    model_name = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(model_name)
    
    context = build_context(report, results, query)
    print(f"\n📊 Context: ~{len(context)//4:,} tokens")
    
    session = model.start_chat(history=[
        {"role": "user", "parts": [f"Research data:\n\n{context}\n\nAnswer questions about this research."]},
        {"role": "model", "parts": ["Ready. What would you like to know?"]}
    ])
    
    print("\n" + "="*50)
    print("💬 Chat (type 'exit' to quit)")
    print("="*50 + "\n")
    
    while True:
        try:
            q = input("You: ").strip()
            if not q:
                continue
            if q.lower() in ['exit', 'quit', 'q']:
                break
            
            response = session.send_message(q)
            print(f"\n🤖 {response.text}\n")
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"Error: {e}\n")


def search(prompt=None, max_iter=5, interactive=True):
    """Run deep search."""
    from deep_search_agent.flow import DeepSearchFlow
    
    prompt = prompt or os.getenv("DEEP_SEARCH_PROMPT", "").strip()
    
    if not prompt:
        print("\n🔍 Deep Search Agent\n" + "-"*40)
        try:
            prompt = input("Query: ").strip()
        except EOFError:
            pass
        prompt = prompt or "latest AI developments"
    
    print(f"\n📝 {prompt}\n")
    
    flow = DeepSearchFlow()
    flow.state.user_prompt = prompt
    flow.state.max_iterations = max_iter
    flow.kickoff()
    
    report = flow.state.final_report or f"# Report\n\n**Query:** {prompt}\n\nNo results."
    results = flow.state.all_results
    
    # Save files
    os.makedirs("reports", exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = slugify(prompt)
    
    Path(f"reports/{name}_{ts}.md").write_text(report)
    Path(f"reports/{name}_{ts}.json").write_text(
        json.dumps({"query": prompt, "results": results}, indent=2, default=str)
    )
    
    print(f"\n📄 reports/{name}_{ts}.md")
    print("\n" + report[:500] + "...\n")
    
    if interactive:
        try:
            if input("💬 Chat? (y/n): ").strip().lower() in ['y', 'yes']:
                chat(report, results, prompt)
        except (EOFError, KeyboardInterrupt):
            pass
    
    return report


def chat_existing(path=None):
    """Chat with existing report."""
    reports = sorted(Path("reports").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not reports:
        print("No reports found.")
        return
    
    if not path:
        print("\nReports:")
        for i, r in enumerate(reports[:5], 1):
            print(f"  {i}. {r.name}")
        try:
            choice = input("\nSelect (1-5): ").strip()
            path = reports[int(choice)-1 if choice else 0]
        except:
            path = reports[0]
    
    path = Path(path)
    report = path.read_text()
    
    # Load JSON data
    results, query = [], path.stem
    json_path = path.with_suffix(".json")
    if json_path.exists():
        data = json.loads(json_path.read_text())
        results = data.get("results", [])
        query = data.get("query", query)
    
    print(f"📄 {path.name}")
    chat(report, results, query)


def run():
    """Entry point for crewai run."""
    return search()


def kickoff(inputs=None):
    """Entry point with inputs."""
    inputs = inputs or {}
    return search(inputs.get("prompt"), inputs.get("max_iterations", 5), inputs.get("interactive", False))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--prompt")
    p.add_argument("-i", "--iterations", type=int, default=5)
    p.add_argument("-c", "--chat", nargs="?", const="")
    p.add_argument("--no-chat", action="store_true")
    args = p.parse_args()
    
    if args.chat is not None:
        chat_existing(args.chat or None)
    else:
        search(args.prompt, args.iterations, not args.no_chat)


if __name__ == "__main__":
    main()
