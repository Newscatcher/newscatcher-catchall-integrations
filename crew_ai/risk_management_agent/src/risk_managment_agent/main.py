#!/usr/bin/env python
"""Automotive Supply Chain Risk Management System"""

import sys
import os
import json
import time
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_QUERY = "Supply chain disruptions and logistics delays from suppliers affecting production at car manufacturers in EU"
DEFAULT_CONTEXT = "Focus on logistics bottlenecks, transport delays, semiconductor shortages, raw material scarcity, labour strikes, and geopolitical disruptions"
DEFAULT_SCHEMA = "Supplier [NAME] Event [SHORT_EVENT_NAME] Impact [SHORT_DESCRIPTION_OF_IMPACT_ON_PRODUCTION_OR_SUPPLY] Severity [High / Medium / Low]"


def get_client():
    """Get Newscatcher API client."""
    from newscatcher_catchall import CatchAllApi
    
    api_key = os.getenv("NEWSCATCHER_API_KEY")
    if not api_key:
        raise ValueError("NEWSCATCHER_API_KEY not set")
    return CatchAllApi(api_key=api_key)


def fetch_from_monitor(monitor_id: str) -> dict:
    """Fetch results from an existing monitor."""
    client = get_client()
    
    sys.stdout.write(f"Fetching from monitor: {monitor_id}\n")
    sys.stdout.flush()
    
    results = client.monitors.pull_monitor_results(monitor_id)
    return convert_results(results)


def fetch_from_job(job_id: str) -> dict:
    """Fetch results from an existing job."""
    client = get_client()
    
    sys.stdout.write(f"Fetching from job: {job_id}\n")
    sys.stdout.flush()
    
    results = client.jobs.get_job_results(job_id)
    return convert_results(results)


def create_new_job() -> dict:
    """Create a new job and wait for completion."""
    client = get_client()
    
    sys.stdout.write("Creating new job...\n")
    sys.stdout.flush()
    
    job = client.jobs.create_job(
        query=DEFAULT_QUERY,
        context=DEFAULT_CONTEXT,
        schema=DEFAULT_SCHEMA,
    )
    sys.stdout.write(f"Job created: {job.job_id}\n")
    sys.stdout.flush()
    
    while True:
        status = client.jobs.get_job_status(job.job_id)
        completed = any(s.status == "completed" and s.completed for s in status.steps)
        
        if completed:
            sys.stdout.write("Job completed!\n")
            sys.stdout.flush()
            break
        
        current_step = next((s for s in status.steps if not s.completed), None)
        if current_step:
            sys.stdout.write(f"Processing: {current_step.status} (step {current_step.order}/7)\n")
            sys.stdout.flush()
        
        time.sleep(30)
    
    results = client.jobs.get_job_results(job.job_id)
    return convert_results(results)


def to_dict(obj):
    """Convert object to dict recursively."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(i) for i in obj]
    if hasattr(obj, 'model_dump'):
        return to_dict(obj.model_dump())
    if hasattr(obj, '__dict__'):
        return {k: to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
    return str(obj)


def convert_results(results) -> dict:
    """Convert API results to dict format."""
    data = to_dict(results)
    
    # Normalize field names (monitor vs job)
    if 'monitor_id' in data and 'job_id' not in data:
        data['job_id'] = data['monitor_id']
    
    data.setdefault('valid_records', len(data.get('all_records', [])))
    data.setdefault('date_range', {'start_date': '', 'end_date': ''})
    data.setdefault('query', '')
    data.setdefault('status', 'completed')
    
    return data


def prompt_user() -> tuple:
    """Prompt user for data source selection."""
    print("\n" + "=" * 50)
    print("📊 DATA SOURCE SELECTION")
    print("=" * 50)
    print("1. Fetch from Monitor (continuous monitoring)")
    print("2. Fetch from existing Job ID")
    print("3. Create new Job (takes ~4-5 minutes)")
    print("=" * 50)
    
    choice = input("Select option [1/2/3]: ").strip()
    
    if choice == "1":
        monitor_id = input("Enter Monitor ID: ").strip()
        return "monitor", monitor_id
    elif choice == "2":
        job_id = input("Enter Job ID: ").strip()
        return "job", job_id
    elif choice == "3":
        return "new", None
    else:
        print("Invalid choice, defaulting to new job")
        return "new", None


def run(mode: str = None, source_id: str = None):
    """Run the risk management crew."""
    from risk_managment_agent.crew import RiskManagmentAgent
    
    sys.stdout.write("=" * 70 + "\n")
    sys.stdout.write("🚗 AUTOMOTIVE SUPPLY CHAIN RISK MANAGEMENT\n")
    sys.stdout.write("=" * 70 + "\n\n")
    sys.stdout.flush()
    
    # Determine data source
    if mode is None:
        mode, source_id = prompt_user()
    
    # Fetch data based on mode
    if mode == "monitor":
        news_data = fetch_from_monitor(source_id)
    elif mode == "job":
        news_data = fetch_from_job(source_id)
    else:
        news_data = create_new_job()
    
    
    sys.stdout.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
    sys.stdout.write(f"Records: {news_data['valid_records']}\n")
    sys.stdout.write("=" * 70 + "\n\n")
    sys.stdout.flush()
    
    inputs = {
        'target_manufacturers': 'car manufacturers in EU',
        'current_year': str(datetime.now().year),
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'news_data': json.dumps(news_data, indent=2),
        'valid_records': str(news_data['valid_records']),
        'date_range_start': news_data['date_range']['start_date'],
        'date_range_end': news_data['date_range']['end_date'],
        'focus_areas': 'semiconductor shortages, raw material scarcity, logistics delays, labor strikes, geopolitical disruptions',
    }
    
    try:
        result = RiskManagmentAgent().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"Error running crew: {e}")
    finally:
        sys.stdout.write("\n" + "=" * 70 + "\n")
        sys.stdout.write("✅ Analysis complete. Report saved to reports/\n")
        sys.stdout.write("=" * 70 + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    # CLI: python main.py [monitor|job|new] [id]
    if len(sys.argv) >= 2:
        mode = sys.argv[1]
        source_id = sys.argv[2] if len(sys.argv) > 2 else None
        run(mode, source_id)
    else:
        run()
