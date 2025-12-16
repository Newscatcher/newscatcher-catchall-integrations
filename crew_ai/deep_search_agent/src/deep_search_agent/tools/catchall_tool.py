"""CatchAll API tool for news search."""

import os
import time
import json
from datetime import datetime
from typing import Type, Any, Dict, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class CatchAllSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    context: Optional[str] = Field(default=None)
    extraction_schema: Optional[str] = Field(default=None)


class CatchAllSearchTool(BaseTool):
    name: str = "catchall_search"
    description: str = "Search news via CatchAll API"
    args_schema: Type[BaseModel] = CatchAllSearchInput
    
    def _run(self, query: str, context: Optional[str] = None, extraction_schema: Optional[str] = None, **_) -> str:
        try:
            from newscatcher_catchall import CatchAllApi
            
            api_key = os.getenv("NEWSCATCHER_API_KEY")
            if not api_key:
                return json.dumps({"error": "NEWSCATCHER_API_KEY not set", "valid_records": 0, "all_records": []})
            
            print(f"\n🔍 {query[:70]}...")
            
            client = CatchAllApi(api_key=api_key)
            
            params = {"query": query}
            if context:
                params["context"] = context
            if extraction_schema:
                params["schema"] = extraction_schema
            
            job = client.jobs.create_job(**params)
            print(f"   Job {job.job_id}")
            
            # Wait for completion (30 min max)
            for elapsed in range(0, 1800, 30):
                status = client.jobs.get_job_status(job.job_id)
                
                if any(s.status == "completed" and s.completed for s in status.steps):
                    break
                if all(s.completed for s in status.steps):
                    break
                
                current = next((s for s in status.steps if not s.completed), None)
                if current:
                    print(f"   [{elapsed//60}m] {current.status}")
                
                time.sleep(30)
            else:
                return json.dumps({"error": "timeout", "valid_records": 0, "all_records": []})
            
            results = client.jobs.get_job_results(job.job_id)
            data = self._convert(results)
            data["query"] = query
            print(f"   ✓ {data.get('valid_records', 0)} records")
            
            return json.dumps(data, indent=2)
            
        except Exception as e:
            print(f"   ✗ {e}")
            return json.dumps({"error": str(e), "valid_records": 0, "all_records": []})
    
    def _convert(self, obj) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._convert(i) for i in obj]
        if hasattr(obj, "model_dump"):
            return self._convert(obj.model_dump())
        if hasattr(obj, "__dict__"):
            return {k: self._convert(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
        return str(obj)


class SearchResultFormatter:
    @staticmethod
    def format_results(data: Dict[str, Any]) -> str:
        lines = [f"**Query:** {data.get('query', '')}", f"**Records:** {data.get('valid_records', 0)}\n"]
        
        for i, rec in enumerate(data.get("all_records", []), 1):
            lines.append(f"## {i}. {rec.get('record_title', 'Untitled')}")
            
            enr = rec.get("enrichment", {})
            if enr.get("schema_based_summary"):
                lines.append(f"{enr['schema_based_summary']}\n")
            
            for k in ["affected_manufacturers", "disruption_causes"]:
                if enr.get(k):
                    lines.append(f"**{k.replace('_', ' ').title()}:** {enr[k]}")
            
            cites = rec.get("citations", [])[:3]
            if cites:
                lines.append("**Sources:** " + ", ".join(f"[{c.get('title', '')[:40]}]({c.get('link', '')})" for c in cites))
            lines.append("")
        
        return "\n".join(lines)
