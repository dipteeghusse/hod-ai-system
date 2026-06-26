"""Task Planner Agent — creates daily/weekly/monthly/semester task plans."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


PLANNER_TOOLS_PROMPT = """When generating task plans, output a JSON array of task objects like:
[
  {
    "title": "Task title",
    "description": "Detailed description",
    "priority": "high|medium|low|critical",
    "category": "academic|research|administrative|nba|events|examination",
    "estimated_days": 3,
    "suggested_assignee_role": "faculty|hod|lab_assistant|office_staff",
    "tags": ["tag1", "tag2"]
  }
]
After the JSON, provide a brief human-readable summary."""


class TaskPlannerAgent(BaseAgent):
    name = "task_planner"
    description = "Creates structured task plans from academic calendars, circulars, and events"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Task Planning agent for the CSE-AIML department. "
            "You create comprehensive, actionable task plans based on academic calendars, "
            "university circulars, NBA/NAAC requirements, departmental events, and deadlines. "
            "You break down large activities into specific, assignable tasks with priorities and timelines."
        ) + "\n\n" + PLANNER_TOOLS_PROMPT

    @traceable(name="task_planner_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Context:\n{context}\n\nPlanning Request: {query}"),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def generate_daily_plan(self, date_str: str, rag_context: str) -> dict:
        raw = self.invoke(
            f"Generate a complete daily task plan for {date_str}. Include all recurring "
            "department activities, any upcoming deadlines within 7 days, and NBA/NAAC items.",
            context=rag_context,
        )
        return self._parse_plan(raw)

    def generate_weekly_plan(self, week_start: str, rag_context: str) -> dict:
        raw = self.invoke(
            f"Generate a weekly task plan starting from {week_start}. "
            "Organize tasks by day and priority. Include faculty meetings, reviews, and reports.",
            context=rag_context,
        )
        return self._parse_plan(raw)

    def plan_from_circular(self, circular_text: str) -> dict:
        raw = self.invoke(
            "Extract all action items from this university circular and create a task plan "
            "with realistic deadlines and responsible roles.",
            context=f"Circular Content:\n{circular_text}",
        )
        return self._parse_plan(raw)

    def _parse_plan(self, raw: str) -> dict:
        tasks = []
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                tasks = json.loads(raw[start:end])
        except Exception:
            pass
        return {"tasks": tasks, "summary": raw}
