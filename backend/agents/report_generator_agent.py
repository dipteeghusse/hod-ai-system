"""Report Generator Agent — weekly, monthly, semester, IQAC reports."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class ReportGeneratorAgent(BaseAgent):
    name = "report_generator"
    description = "Auto-generates department reports in structured format"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Report Generation agent. You automatically generate professional "
            "department reports: weekly, monthly, semester, IQAC, and Principal reports. "
            "Reports must follow MITAOE official format with proper sections, tables, and summaries. "
            "Use data-driven language with KPIs, metrics, and trend analysis."
        )

    @traceable(name="report_generator_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Report Data:\n{context}\n\nReport Request: {query}"),
        ]
        return self.llm.invoke(messages).content

    def generate_weekly_report(self, week_data: dict) -> str:
        return self.invoke(
            f"Generate a formal Weekly Department Report for {settings.DEPARTMENT}. "
            "Include: Executive Summary, Tasks Completed, Tasks Pending, "
            "Faculty Activities, Events, Achievements, Issues/Risks, Next Week Plan. "
            "Format with proper headings and tables.",
            context=json.dumps(week_data, indent=2),
        )

    def generate_monthly_report(self, month_data: dict) -> str:
        return self.invoke(
            "Generate a comprehensive Monthly Department Report. Include: "
            "Task completion metrics, Faculty performance summary, Student activities, "
            "Research output, Events conducted, NBA/NAAC progress, KPIs dashboard, "
            "Challenges faced, Action taken, Plan for next month.",
            context=json.dumps(month_data, indent=2),
        )

    def generate_iqac_report(self, semester_data: dict) -> str:
        return self.invoke(
            "Generate an IQAC Semester Report for the department. Follow standard IQAC format: "
            "Teaching-Learning innovations, Student performance analysis, Research activities, "
            "Faculty development, Best practices, Future plans. "
            "Include quantitative data with graphs description.",
            context=json.dumps(semester_data, indent=2),
        )

    def generate_principal_report(self, department_kpis: dict) -> str:
        return self.invoke(
            "Generate a concise Principal's Monthly Report. Include: "
            "Department health score, Key achievements, Pending critical items, "
            "Faculty highlights, Student success stories, Resource needs, Risks. "
            "Keep it executive-level: brief, impactful, data-driven.",
            context=json.dumps(department_kpis, indent=2),
        )

    def generate_faculty_performance_report(self, faculty_data: list) -> str:
        return self.invoke(
            "Generate a Faculty Performance Analysis Report. Include individual scorecards, "
            "API points summary, teaching load analysis, research output, "
            "FDP attendance, and comparative ranking. Suggest improvement areas.",
            context=json.dumps(faculty_data, indent=2),
        )
