"""Automotive Supply Chain Risk Management Crew"""

import os
from datetime import datetime
from typing import List, Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from risk_managment_agent.tools.newscatcher_risk_tool import NewscatcherDirectResultTool


@CrewBase
class RiskManagmentAgent:
    """3-stage risk management pipeline for EU automotive OEMs."""

    agents: List[BaseAgent]
    tasks: List[Task]
    _gemini_llm: Optional[LLM] = None
    
    @property
    def gemini_llm(self) -> LLM:
        if self._gemini_llm is None:
            self._gemini_llm = LLM(
                model=os.getenv("MODEL", "gemini/gemini-2.5-flash"),
                api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
                temperature=0.2,
            )
        return self._gemini_llm
    
    @agent
    def news_intelligence_officer(self) -> Agent:
        return Agent(
            config=self.agents_config['news_intelligence_officer'],
            tools=[NewscatcherDirectResultTool()],
            verbose=True,
            llm=self.gemini_llm,
            max_iter=5,
        )
    
    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_analyst'],
            verbose=True,
            llm=self.gemini_llm,
            max_iter=5,
            allow_delegation=False,
        )
    
    @agent
    def executive_report_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['executive_report_analyst'],
            verbose=True,
            llm=self.gemini_llm,
            max_iter=5,
            allow_delegation=False,
        )
    
    @task
    def gather_risk_intelligence(self) -> Task:
        return Task(config=self.tasks_config['gather_risk_intelligence'])
    
    @task
    def analyze_and_categorize_risks(self) -> Task:
        return Task(config=self.tasks_config['analyze_and_categorize_risks'])
    
    @task
    def generate_executive_report(self) -> Task:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Task(
            config=self.tasks_config['generate_executive_report'],
            output_file=f'reports/risk_report_{timestamp}.md',
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            planning=False,
        )
