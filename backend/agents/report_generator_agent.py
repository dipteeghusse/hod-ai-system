"""Report Generator Agent — generic across any department/institution."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class ReportGeneratorAgent(BaseAgent):
    name = "report_generator"
    description = "Auto-generates department reports for any report type or time period"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Report Generation agent. Generate professional department reports "
            "for any report type the user requests.\n\n"
            "Always include: Executive Summary, Key Metrics, Achievements, Pending Items, "
            "Risks/Issues, and Plan for Next Period.\n"
            "Use data-driven language with KPIs, percentages, and trend observations.\n"
            "Adapt section headings to the report type — do not hardcode fixed sections.\n"
            "Never assume fixed subject names; use only what appears in the data provided."
        )

    @traceable(name="report_generator_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Report Data:\n{context}\n\nReport Request:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def generate(self, report_type: str, data: dict, period: str = "") -> str:
        """
        Generic report generator.
        report_type : any string — "weekly", "monthly", "semester", "iqac",
                      "principal", "accreditation", "faculty_performance", etc.
        data        : any dict with task/faculty/event metrics
        period      : human-readable period string e.g. "October 2025"
        """
        period_str = f" for {period}" if period else ""
        return self.invoke(
            f"Generate a {report_type.replace('_', ' ').title()} Report{period_str}. "
            f"Format professionally for {settings.INSTITUTION} — {settings.DEPARTMENT}. "
            "Structure with clear headings, bullet points, and a summary table.",
            context=json.dumps(data, indent=2),
        )

    def generate_weekly(self, data: dict, period: str = "") -> str:
        return self.generate("weekly", data, period)

    def generate_monthly(self, data: dict, period: str = "") -> str:
        return self.generate("monthly", data, period)

    def generate_semester(self, data: dict, period: str = "") -> str:
        return self.generate("semester", data, period)

    def generate_principal(self, data: dict, period: str = "") -> str:
        return self.generate("principal executive", data, period)

    def generate_iqac(self, data: dict, period: str = "") -> str:
        return self.generate("iqac quality assurance", data, period)

    def generate_faculty_performance(self, faculty_data: list, period: str = "") -> str:
        return self.generate(
            "faculty performance analysis",
            {"faculty": faculty_data},
            period,
        )
