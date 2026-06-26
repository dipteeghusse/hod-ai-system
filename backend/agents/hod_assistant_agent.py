"""
HoD Personal Assistant Agent — daily briefings, decision support, and follow-up awareness.
Works in tandem with FollowUpAgent so every morning briefing and evening summary
automatically includes follow-up status for all tasks.
"""

import json
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
            "You are the personal AI executive assistant to the Head of Department.\n\n"
            "Core responsibilities:\n"
            "  1. Daily planning — priorities, time blocks, what to do first.\n"
            "  2. Follow-up awareness — always surface overdue, at-risk, and stale tasks.\n"
            "  3. Morning briefings — concise, action-oriented, ranked by urgency.\n"
            "  4. Evening summaries — what was done, what is still open, plan for tomorrow.\n"
            "  5. Decision support — answer any HoD question using provided context.\n\n"
            "Follow-up rules:\n"
            "  - If any overdue tasks exist, always mention them first.\n"
            "  - Flag faculty with multiple pending or overdue items.\n"
            "  - Suggest specific follow-up actions (call, email, escalate).\n"
            "  - Never downplay urgency — be direct about risks.\n\n"
            "Style: concise, action-oriented, structured with clear headings."
        )

    @traceable(name="hod_assistant_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        now = datetime.now()
        time_ctx = f"Current date/time: {now.strftime('%A, %B %d, %Y %I:%M %p')}"
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"{time_ctx}\n\nContext:\n{context}\n\nQuery:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    # ── Morning Briefing with follow-up ───────────────────────────────────────

    def morning_briefing(self, dashboard_data: dict, followup_summary: dict = {},
                         extra_context: str = "") -> str:
        """
        Generates a morning briefing that includes follow-up status.
        followup_summary: output from FollowUpAgent.classify_tasks()
        """
        ctx = {
            "dashboard": {
                "total_tasks":      dashboard_data.get("total_tasks", 0),
                "pending":          dashboard_data.get("pending_tasks", 0),
                "in_progress":      dashboard_data.get("in_progress_tasks", 0),
                "completed":        dashboard_data.get("completed_tasks", 0),
                "overdue":          dashboard_data.get("overdue_tasks", 0),
                "todays_meetings":  dashboard_data.get("upcoming_meetings", 0),
                "todays_deadlines": dashboard_data.get("today_deadlines", 0),
            },
            "followup": {
                "overdue_count":    followup_summary.get("summary_counts", {}).get("overdue", 0),
                "at_risk_count":    followup_summary.get("summary_counts", {}).get("at_risk", 0),
                "stale_count":      followup_summary.get("summary_counts", {}).get("stale", 0),
                "no_response":      followup_summary.get("summary_counts", {}).get("no_response", 0),
                "top_overdue":      [t.get("title") for t in followup_summary.get("overdue", [])[:5]],
                "faculty_needing_followup": list(followup_summary.get("faculty_followup", {}).keys()),
            },
        }
        return self.invoke(
            "Generate a concise morning briefing. Lead with follow-up items. "
            "Include: top 3 priorities, overdue tasks and their owners, "
            "faculty needing follow-up, today's meetings, and one key recommendation.",
            context=json.dumps(ctx, indent=2) + ("\n\n" + extra_context if extra_context else ""),
        )

    # ── Evening Summary with follow-up ────────────────────────────────────────

    def evening_summary(self, completed_today: list, followup_summary: dict = {}) -> str:
        """
        End-of-day summary highlighting what still needs follow-up tomorrow.
        """
        ctx = {
            "completed_today":        [t.get("title", t) for t in completed_today[:10]],
            "still_overdue":          [t.get("title") for t in followup_summary.get("overdue", [])[:5]],
            "at_risk_tomorrow":       [t.get("title") for t in followup_summary.get("at_risk", [])[:5]],
            "faculty_needing_action": followup_summary.get("faculty_followup", {}),
        }
        return self.invoke(
            "Generate an evening summary. Include: accomplishments today, "
            "unresolved follow-up items, faculty who haven't responded, "
            "and the top 3 priorities for tomorrow.",
            context=json.dumps(ctx, indent=2),
        )

    # ── Quick follow-up digest ────────────────────────────────────────────────

    def followup_digest(self, followup_summary: dict) -> str:
        """
        Short follow-up digest — called any time HoD wants a quick status check.
        Uses the classification output from FollowUpAgent.
        """
        ctx = json.dumps({
            "overdue":          [{"title": t.get("title"), "assignee": t.get("assigned_to_name"),
                                  "days_overdue": t.get("days_overdue")}
                                 for t in followup_summary.get("overdue", [])],
            "at_risk":          [{"title": t.get("title"), "assignee": t.get("assigned_to_name"),
                                  "days_left": t.get("days_left")}
                                 for t in followup_summary.get("at_risk", [])],
            "stale":            [{"title": t.get("title"), "assignee": t.get("assigned_to_name"),
                                  "days_since_update": t.get("days_since_update")}
                                 for t in followup_summary.get("stale", [])],
            "faculty_followup": followup_summary.get("faculty_followup", {}),
        }, indent=2)
        return self.invoke(
            "Give a quick follow-up status digest in bullet points. "
            "Group by: OVERDUE | AT RISK | STALE | FACULTY NEEDING CONTACT. "
            "Keep it under 200 words total.",
            context=ctx,
        )

    # ── General query ─────────────────────────────────────────────────────────

    def answer_query(self, query: str, context: str = "") -> str:
        return self.invoke(query, context=context)
