"""
Follow-Up Agent — analyses ALL tasks and generates structured follow-up summaries.

Covers:
  - Overdue tasks (past due date, not completed)
  - At-risk tasks (due within N days, still pending/delayed)
  - Stale tasks (in_progress but no update for N+ days)
  - No-response tasks (assigned but never moved from pending)
  - Completed tasks pending HoD acknowledgement
  - Faculty-wise follow-up needed list
  - Suggested follow-up message drafts per assignee
"""

import json
from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


def _days_diff(dt_str: str) -> float:
    """Return how many days from now to the given ISO datetime string (negative = past)."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (dt - now).total_seconds() / 86400
    except Exception:
        return 0.0


class FollowUpAgent(BaseAgent):
    name = "followup_agent"
    description = (
        "Generates structured follow-up summaries for all department tasks. "
        "Identifies overdue, at-risk, stale, and no-response items. "
        "Drafts personalised follow-up messages for each assignee."
    )

    def __init__(self, at_risk_days: int = 3, stale_days: int = 5):
        super().__init__()
        self.at_risk_days  = at_risk_days   # warn if due within this many days
        self.stale_days    = stale_days     # flag if no update for this many days
        self._system = self._system_prompt(
            "You are the Follow-Up Assistant for the Head of Department.\n\n"
            "Your job is to analyse the task data provided and produce:\n"
            "1. A concise executive summary of follow-up items.\n"
            "2. A prioritised action list (URGENT → HIGH → MEDIUM).\n"
            "3. A per-faculty follow-up table: who needs what, by when.\n"
            "4. Suggested follow-up message drafts for overdue assignees.\n"
            "5. Recommended next steps for the HoD.\n\n"
            "Always:\n"
            "- Lead with the most urgent items.\n"
            "- Be specific: use task titles, assignee names, and exact dates.\n"
            "- Keep message drafts professional and brief (3–4 sentences).\n"
            "- Do not repeat information unnecessarily.\n"
            "- End with a one-line department health verdict."
        )

    # ── Core classifier ────────────────────────────────────────────────────────

    def classify_tasks(self, tasks: list) -> dict:
        """
        Classify raw task list into follow-up buckets.
        tasks: list of dicts from the DB (title, status, due_date,
               assigned_to_name, updated_at, progress_percentage, category, subject)
        """
        overdue, at_risk, stale, no_response, completed_pending = [], [], [], [], []

        for t in tasks:
            status     = t.get("status", "pending")
            due        = t.get("due_date", "")
            updated    = t.get("updated_at", t.get("created_at", ""))
            assignee   = t.get("assigned_to_name") or "Unassigned"
            progress   = t.get("progress_percentage", 0)
            days_left  = _days_diff(due) if due else None
            days_stale = -_days_diff(updated) if updated else None  # positive = days since last update

            if status == "completed":
                completed_pending.append(t)
                continue

            if status == "overdue" or (days_left is not None and days_left < 0 and status != "completed"):
                overdue.append({**t, "days_overdue": round(abs(days_left or 0), 1)})

            elif days_left is not None and 0 <= days_left <= self.at_risk_days:
                at_risk.append({**t, "days_left": round(days_left, 1)})

            elif (status == "in_progress" and days_stale is not None
                  and days_stale >= self.stale_days):
                stale.append({**t, "days_since_update": round(days_stale, 1)})

            elif status == "pending" and progress == 0:
                no_response.append(t)

        # Faculty-wise rollup
        faculty_map: dict = {}
        for t in overdue + at_risk + stale + no_response:
            name = t.get("assigned_to_name") or "Unassigned"
            faculty_map.setdefault(name, []).append(t.get("title", ""))

        return {
            "overdue":           overdue,
            "at_risk":           at_risk,
            "stale":             stale,
            "no_response":       no_response,
            "completed_today":   completed_pending,
            "faculty_followup":  faculty_map,
            "summary_counts": {
                "overdue":      len(overdue),
                "at_risk":      len(at_risk),
                "stale":        len(stale),
                "no_response":  len(no_response),
                "completed":    len(completed_pending),
            },
        }

    # ── Main invoke ────────────────────────────────────────────────────────────

    @traceable(name="followup_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Task Follow-Up Data:\n{context}\n\nRequest:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    # ── Public methods ─────────────────────────────────────────────────────────

    def full_summary(self, tasks: list) -> dict:
        """
        Main entry point.
        Returns classification dict + AI-generated narrative summary.
        """
        classified = self.classify_tasks(tasks)
        now_str    = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

        context = json.dumps({
            "generated_at":        now_str,
            "department":          settings.DEPARTMENT,
            "institution":         settings.INSTITUTION,
            "at_risk_threshold":   f"{self.at_risk_days} days",
            "stale_threshold":     f"{self.stale_days} days without update",
            **classified,
        }, indent=2)

        narrative = self.invoke(
            "Generate a complete follow-up summary report for the HoD. "
            "Include all sections: executive summary, prioritised action list, "
            "per-faculty table, message drafts, and next steps.",
            context=context,
        )
        return {**classified, "narrative": narrative, "generated_at": now_str}

    def per_faculty_summary(self, faculty_name: str, tasks: list) -> str:
        """Follow-up summary scoped to one faculty member."""
        classified = self.classify_tasks(tasks)
        relevant   = [t for t in tasks if t.get("assigned_to_name") == faculty_name]
        return self.invoke(
            f"Generate a follow-up summary specifically for {faculty_name}. "
            "List their overdue, at-risk, and stale tasks. "
            "Draft a polite but firm follow-up message the HoD can send.",
            context=json.dumps({"faculty": faculty_name, "tasks": relevant}, indent=2),
        )

    def draft_followup_message(self, assignee_name: str, task_titles: list,
                                urgency: str = "high") -> str:
        """Draft a follow-up message for a specific assignee."""
        return self.invoke(
            f"Draft a professional follow-up message from the HoD to {assignee_name}. "
            f"Urgency: {urgency}. "
            f"Tasks requiring follow-up: {', '.join(task_titles)}. "
            "Keep it polite, specific, and under 100 words.",
            context=f"Department: {settings.DEPARTMENT}, Institution: {settings.INSTITUTION}",
        )

    def priority_actions(self, tasks: list, top_n: int = 5) -> str:
        """Return the top N highest-priority follow-up actions only."""
        classified = self.classify_tasks(tasks)
        context    = json.dumps({
            "top_overdue":    classified["overdue"][:top_n],
            "top_at_risk":    classified["at_risk"][:top_n],
        }, indent=2)
        return self.invoke(
            f"List only the top {top_n} follow-up actions the HoD must take today. "
            "Be extremely concise — one line per action with owner and deadline.",
            context=context,
        )
