# Automotive Supply Chain Risk Management
    
CrewAI multi-agent system for monitoring supply chain risks affecting automotive OEMs in the EU.

## Setup

Follow the installation instructions here: https://docs.crewai.com/en/installation
    
```bash
cd deep_search_agent
crewai install
```

Create `.env`:
```
MODEL=gemini/gemini-2.5-flash
NEWSCATCHER_API_KEY=your-key
GEMINI_API_KEY=your-key
```


## Usage

### Interactive Mode (prompts for data source)
```bash
crewai run
```

### CLI Mode
```bash
# Fetch from monitor
python -m risk_managment_agent.main monitor <monitor_id>

# Fetch from existing job
python -m risk_managment_agent.main job <job_id>

# Create new job
python -m risk_managment_agent.main new
```

### Examples
```bash
# From monitor
python -m risk_managment_agent.main monitor <monitor_id>

# From job
python -m risk_managment_agent.main job <job_id>
```

## Pipeline

1. **Intelligence Officer** - Extracts risk signals from news data
2. **Risk Analyst** - Categorizes risks by type and severity
3. **Executive Analyst** - Creates categorized report with impact

## Output

Reports: `reports/risk_report_YYYYMMDD_HHMMSS.md`

## Risk Categories

- Semiconductor Shortage
- Raw Material Scarcity
- Logistics Delay
- Labor Disruption
- Geopolitical
- Supplier Financial
- Energy Crisis
- Competition
