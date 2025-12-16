"""Crews for deep search workflow."""

import os
from crewai import Agent, Crew, Process, Task, LLM


def llm(temp=0.3):
    return LLM(
        model=os.getenv("MODEL", "gemini/gemini-2.5-flash"),
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        temperature=temp,
    )


class QueryPlannerCrew:
    def crew(self):
        agent = Agent(
            role="Query Specialist",
            goal="Create effective search queries",
            backstory=(
                "Expert at CatchAll queries. Rules: simple natural language, "
                "one event type, no dates/operators. "
                "Examples: 'AI acquisitions', 'supply chain disruptions at automakers'"
            ),
            llm=llm(0.3),
            verbose=True,
            max_iter=3,
        )
        
        task = Task(
            description=(
                "Query for: {user_prompt}\n"
                "Iteration {iteration_number}/{max_iterations}\n"
                "Previous: {previous_queries}\n"
                "Results: {previous_results_summary}\n"
                "If retrying, use broader terms."
            ),
            expected_output='{"query": "...", "context": "...", "schema": "...", "reasoning": "..."}',
            agent=agent,
        )
        
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)


class ResultEvaluatorCrew:
    def crew(self):
        agent = Agent(
            role="Quality Analyst",
            goal="Evaluate search result quality",
            backstory="Assesses if results answer the query adequately.",
            llm=llm(0.2),
            verbose=True,
            max_iter=3,
        )
        
        task = Task(
            description="Evaluate: {user_prompt}\nQuery: {current_query}\nResults: {search_results}",
            expected_output='{"is_sufficient": bool, "quality_score": 1-10, "gaps": [...]}',
            agent=agent,
        )
        
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)


class ResearchSynthesizerCrew:
    def crew(self):
        agent = Agent(
            role="Research Writer",
            goal="Create comprehensive research reports",
            backstory="Writes clear reports with findings, citations, and conclusions.",
            llm=llm(0.4),
            verbose=True,
            max_iter=5,
        )
        
        task = Task(
            description=(
                "Report for: {user_prompt}\n\n"
                "Data:\n{all_results}\n\n"
                "Include: summary, key findings, sources, conclusions."
            ),
            expected_output="Markdown report with citations",
            agent=agent,
        )
        
        return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
