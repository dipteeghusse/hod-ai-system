"""HoD Personal Assistant Agent — daily briefings, priorities, calendar awareness."""

from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from datetime import datetime
from agents.base_agent import BaseAgent


class HoDAssistantAgent(BaseAgent):
    name = "hod_assistant"
    description = "Personal AI assistant for the Head of Department"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the personal AI executive assistant to the Head of Department. "
            "You help with daily planning, priority setting, briefings, and decision support. "
            "You have knowledge of all department tasks, meetings, faculty status, and deadlines. "
            "Provide morning briefings, evening summaries, and answer any HOD queries."
        )

    @traceable(name="hod_assistant_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        now = datetime.now()
        time_context = f"Current date/time: {now.strftime('%A, %B %d, %Y %I:%M %p')}"

        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"{time_context}\n\nDepartment Context:\n{context}\n\nHoD Query: {query}"),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def morning_briefing(self, dashboard_data: dict, rag_context: str) -> str:
        summary = f"""
Today's Overview:
- Total Tasks: {dashboard_data.get('total_tasks', 0)}
- Pending: {dashboard_data.get('pending_tasks', 0)}
- Overdue: {dashboard_data.get('overdue_tasks', 0)}
- Meetings Today: {dashboard_data.get('upcoming_meetings', 0)}
- Today's Deadlines: {dashboard_data.get('today_deadlines', 0)}
"""
        return self.invoke(
            "Generate a concise morning briefing for the HoD. Highlight critical priorities, "
            "overdue items, and what needs immediate attention today.",
            context=summary + "\n\n" + rag_context,
        )

    def evening_summary(self, completed_today: list, pending: list) -> str:
        context = f"Completed today: {len(completed_today)} tasks\nStill pending: {len(pending)} tasks"
        return self.invoke(
            "Generate an end-of-day summary. What was accomplished, what is still pending, "
            "and what should be the top priorities for tomorrow?",
            context=context,
        )
