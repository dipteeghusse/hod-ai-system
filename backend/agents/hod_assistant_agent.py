"""HoD Personal Assistant Agent — generic, context-driven briefings and decision support."""

from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from datetime import datetime
from agents.base_agent import BaseAgent
from config import settings


class HoDAssistantAgent(BaseAgent):
    name = "hod_assistant"
    description = "Personal AI executive assistant to the Head of Department"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the personal AI executive assistant to the Head of Department.\n"
            "Help with: daily planning, priority setting, morning briefings, evening summaries, "
            "and decision support.\n"
            "You have access to all department tasks, meetings, faculty status, and deadlines "
            "provided in the context.\n"
            "Adapt your tone and content to the department's actual subjects and activities — "
            "never invent tasks or subjects not present in the context."
        )

    @traceable(name="hod_assistant_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        now = datetime.now()
        time_ctx = f"Current date/time: {now.strftime('%A, %B %d, %Y %I:%M %p')}"
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"{time_ctx}\n\nDepartment Data:\n{context}\n\nQuery:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def morning_briefing(self, dashboard_data: dict, extra_context: str = "") -> str:
        ctx = (
            f"Total Tasks: {dashboard_data.get('total_tasks', 0)}\n"
            f"Pending: {dashboard_data.get('pending_tasks', 0)}\n"
            f"Overdue: {dashboard_data.get('overdue_tasks', 0)}\n"
            f"Today's Meetings: {dashboard_data.get('upcoming_meetings', 0)}\n"
            f"Today's Deadlines: {dashboard_data.get('today_deadlines', 0)}\n"
        )
        return self.invoke(
            "Generate a concise morning briefing. Highlight: top 3 priorities, "
            "overdue items needing immediate action, and any meetings today.",
            context=ctx + ("\n" + extra_context if extra_context else ""),
        )

    def evening_summary(self, completed_count: int, pending_list: list) -> str:
        ctx = (
            f"Completed today: {completed_count}\n"
            f"Still pending ({len(pending_list)}): "
            + ", ".join(t.get("title", "") for t in pending_list[:10])
        )
        return self.invoke(
            "Generate an end-of-day summary: what was accomplished, what is pending, "
            "and the top 3 priorities for tomorrow.",
            context=ctx,
        )

    def answer_query(self, query: str, context: str = "") -> str:
        """Catch-all for any HoD question — fully driven by user query and provided context."""
        return self.invoke(query, context=context)
