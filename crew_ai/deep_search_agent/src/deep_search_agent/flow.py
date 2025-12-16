"""Deep Search Flow - Iterative search with report synthesis."""

import json
import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start

from deep_search_agent.tools.catchall_tool import CatchAllSearchTool, SearchResultFormatter
from deep_search_agent.crews import QueryPlannerCrew, ResearchSynthesizerCrew


class SearchIteration(BaseModel):
    iteration: int
    query: str
    context: Optional[str] = None
    schema: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    records_found: int = 0


class DeepSearchState(BaseModel):
    user_prompt: str = ""
    max_iterations: int = 5
    current_iteration: int = 0
    iterations: List[SearchIteration] = Field(default_factory=list)
    all_results: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int = 0
    final_report: str = ""


class DeepSearchFlow(Flow[DeepSearchState]):
    
    def __init__(self):
        super().__init__()
        self.tool = CatchAllSearchTool()
    
    @start()
    def search_loop(self):
        """Run search iterations until results found or max reached."""
        print(f"\n{'='*50}\n🔍 {self.state.user_prompt[:50]}...\n{'='*50}")
        
        while self.state.current_iteration < self.state.max_iterations:
            self.state.current_iteration += 1
            print(f"\n--- Iteration {self.state.current_iteration}/{self.state.max_iterations} ---")
            
            # Plan and execute
            plan = self._plan()
            it = SearchIteration(
                iteration=self.state.current_iteration,
                query=plan.get("query", ""),
                context=plan.get("context"),
                schema=plan.get("schema"),
            )
            self.state.iterations.append(it)
            
            # Search
            result = self._search(it)
            it.results = result
            it.records_found = result.get("valid_records", 0)
            
            if it.records_found > 0:
                self.state.all_results.append(result)
                self.state.total_records += it.records_found
                print(f"   ✓ {it.records_found} records")
                break
            
            print("   ✗ No results, retrying...")
        
        print(f"\n{'='*50}\n✓ {self.state.total_records} total records\n{'='*50}")
    
    @listen(search_loop)
    def synthesize(self):
        """Create final report."""
        print("\n📝 Creating report...")
        
        if not self.state.total_records:
            queries = "\n".join(f"- {it.query}" for it in self.state.iterations)
            self.state.final_report = f"# Report\n\n**Query:** {self.state.user_prompt}\n\nNo results after {self.state.current_iteration} attempts.\n\n## Queries tried\n{queries}"
            return
        
        formatted = "\n\n".join(
            SearchResultFormatter.format_results(r) for r in self.state.all_results
        )
        
        result = ResearchSynthesizerCrew().crew().kickoff(inputs={
            "user_prompt": self.state.user_prompt,
            "all_results": formatted,
            "iterations_summary": "\n".join(
                f"- {it.query[:40]}... → {it.records_found}" for it in self.state.iterations
            ),
        })
        
        self.state.final_report = str(result)
        print(f"   ✓ {len(self.state.final_report)} chars")
    
    @listen(synthesize)
    def done(self):
        return self.state.final_report
    
    def _plan(self):
        prev = "\n".join(f"- {it.query}" for it in self.state.iterations) or "None"
        results = "\n".join(f"- {it.query[:30]}... → {it.records_found}" for it in self.state.iterations) or "None"
        
        out = QueryPlannerCrew().crew().kickoff(inputs={
            "user_prompt": self.state.user_prompt,
            "iteration_number": str(self.state.current_iteration),
            "max_iterations": str(self.state.max_iterations),
            "previous_queries": prev,
            "previous_results_summary": results,
        })
        
        plan = self._extract_json(str(out)) or {"query": self.state.user_prompt}
        
        for k in ["schema", "context"]:
            if isinstance(plan.get(k), dict):
                plan[k] = json.dumps(plan[k])
        
        print(f"   Query: {plan['query'][:60]}...")
        return plan
    
    def _search(self, it):
        result = self.tool._run(it.query, it.context, it.schema)
        try:
            return json.loads(result)
        except:
            return {"valid_records": 0, "all_records": []}
    
    def _extract_json(self, text):
        for pattern in [r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```', r'\{[\s\S]*\}']:
            m = re.search(pattern, text)
            if m:
                try:
                    return json.loads(m.group(1) if m.lastindex else m.group(0))
                except:
                    continue
        return None
