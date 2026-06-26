"""Task Planner Agent — generic across any department, subjects, and categories."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class TaskPlannerAgent(BaseAgent):
    name = "task_planner"
    description = "Creates structured task plans from any academic calendar, circular, or event input"

    def __init__(self):
        super().__init__()
        categories = ", ".join(settings.task_categories_list)
        self._system = self._system_prompt(
            f"You are the Task Planning agent. Create actionable task plans from "
            f"academic calendars, circulars, events, and deadlines provided by the user.\n\n"
            f"Available task categories: {categories}\n\n"
            f"For every task output a JSON array item with fields:\n"
            f"  title, description, priority (low|medium|high|critical), "
            f"  category (from the list above), estimated_days (int), "
            f"  suggested_assignee_role (faculty|hod|lab_assistant|office_staff|student), "
            f"  tags (list of strings)\n\n"
            f"After the JSON array, add a brief plain-English summary.\n"
            f"Use ONLY the subjects/courses and categories provided in the department context — "
            f"do not invent new ones."
        )

    @traceable(name="task_planner_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Context:\n{context}\n\nPlanning Request:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def generate_daily_plan(self, date_str: str, rag_context: str = "") -> dict:
        raw = self.invoke(
            f"Generate a complete daily task plan for {date_str}. "
            "Include recurring department activities and any upcoming deadlines within 7 days.",
            context=rag_context,
        )
        return self._parse(raw)

    def generate_weekly_plan(self, week_start: str, rag_context: str = "") -> dict:
        raw = self.invoke(
            f"Generate a weekly task plan starting {week_start}. "
            "Organise tasks by day and priority. Include faculty meetings, reviews, and reports.",
            context=rag_context,
        )
        return self._parse(raw)

    def plan_from_text(self, input_text: str) -> dict:
        """
        Generic planner — accepts ANY free-text input:
        circular, email, meeting notes, event description, deadline list, etc.
        """
        raw = self.invoke(
            "Extract all action items from the text below and create a prioritised task plan. "
            "Assign realistic deadlines and responsible roles based on department context.",
            context=f"Input Text:\n{input_text}",
        )
        return self._parse(raw)

    def _parse(self, raw: str) -> dict:
        tasks = []
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            if start >= 0 and end > start:
                tasks = json.loads(raw[start:end])
        except Exception:
            pass
        return {"tasks": tasks, "summary": raw}
