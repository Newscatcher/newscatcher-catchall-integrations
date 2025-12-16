"""Newscatcher Catch-All API Tool for processing risk intelligence data."""

import json
import re
from typing import Type, Any, Dict

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class NewscatcherDirectResultInput(BaseModel):
    results_json: str = Field(..., description="JSON string containing Newscatcher job results")


class NewscatcherDirectResultTool(BaseTool):
    """Processes pre-fetched Newscatcher Catch-All API results for risk analysis."""
    
    name: str = "newscatcher_process_results"
    description: str = "Processes Newscatcher API results to extract supply chain risks."
    args_schema: Type[BaseModel] = NewscatcherDirectResultInput
    
    def _run(self, results_json: str) -> str:
        try:
            # Try to fix common JSON issues
            fixed_json = self._fix_json(results_json)
            data = json.loads(fixed_json)
            return self._format_results(data)
        except json.JSONDecodeError as e:
            # If JSON still fails, try to extract what we can
            return self._extract_from_malformed(results_json, str(e))
        except Exception as e:
            return f"Error: {e}"
    
    def _fix_json(self, json_str: str) -> str:
        """Attempt to fix common JSON issues."""
        # Fix truncated strings
        json_str = re.sub(r'"\s*$', '"}', json_str)
        # Fix missing commas before quotes
        json_str = re.sub(r'"\s+"', '", "', json_str)
        return json_str
    
    def _extract_from_malformed(self, raw: str, error: str) -> str:
        """Extract useful info even from malformed JSON."""
        output = ["## Risk Intelligence (Partial Extraction)", f"Note: JSON parsing error - {error}", ""]
        
        # Extract record titles using regex
        titles = re.findall(r'"record_title":\s*"([^"]+)"', raw)
        if titles:
            output.append("### Identified Risk Events:")
            for i, title in enumerate(titles, 1):
                output.append(f"{i}. {title}")
        
        # Extract citation titles
        citations = re.findall(r'"title":\s*"([^"]+)"', raw)
        if citations:
            output.append("\n### News Sources Found:")
            for title in citations[:20]:  # Limit to first 20
                output.append(f"- {title}")
        
        return "\n".join(output)
    
    def _format_results(self, data: Dict[str, Any]) -> str:
        output = []
        output.append("## Risk Intelligence Results")
        output.append(f"**Records:** {data.get('valid_records', len(data.get('all_records', [])))}")
        output.append("")
        
        for i, record in enumerate(data.get('all_records', []), 1):
            title = record.get('record_title', 'Untitled')
            output.append(f"### {i}. {title}")
            
            enrichment = record.get('enrichment', {})
            if enrichment:
                summary = enrichment.get('schema_based_summary')
                if summary:
                    output.append(f"**Summary:** {summary}")
                
                mfrs = enrichment.get('affected_manufacturers')
                if mfrs:
                    output.append(f"**Manufacturers:** {mfrs}")
                
                causes = enrichment.get('disruption_causes')
                if causes:
                    output.append(f"**Causes:** {causes}")
                
                components = enrichment.get('affected_components')
                if components:
                    output.append(f"**Components:** {components}")
                
                impact = enrichment.get('impact_details')
                if impact and isinstance(impact, dict):
                    output.append("**Impact:**")
                    for k, v in impact.items():
                        if v:
                            output.append(f"  - {k}: {v}")
            
            citations = record.get('citations', [])
            if citations:
                output.append("**Sources:**")
                for c in citations[:3]:  # Limit to 3 sources per record
                    title = c.get('title', '')
                    link = c.get('link', '')
                    if title:
                        output.append(f"  - [{title}]({link})")
            
            output.append("")
        
        return "\n".join(output)
