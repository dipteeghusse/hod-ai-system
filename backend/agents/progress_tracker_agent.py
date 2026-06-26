"""Progress Tracker Agent — generic task monitoring across any categories and subjects."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class ProgressTrackerAgent(BaseAgent):
    name = "progress_tracker"
    description = "Monitors task progress, flags delays/risks, generates status reports"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Progress Tracking agent.\n"
            "Monitor departmental tasks, identify delays and risks, compute completion rates, "
            "and generate actionable status reports for the HoD.\n\n"
            "Tasks can belong to any category defined in the department config. "
            "Statuses are: pending, in_progress, completed, delayed, overdue.\n"
            "Always provide: overall health assessment, risk items, staff needing follow-up, "
            "and concrete recommendations."
        )

    @traceable(name="progress_tracker_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Task Data:\n{context}\n\nTracking Query:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def analyze_progress(self, tasks: list) -> dict:
        if not tasks:
            return {"analysis": "No tasks to analyse.", "risk_items": [], "stats": {}}

        status_counts: dict = {}
        priority_counts: dict = {}
        category_counts: dict = {}
        overdue, at_risk = [], []

        for t in tasks:
            s = t.get("status", "pending")
            status_counts[s] = status_counts.get(s, 0) + 1
            p = t.get("priority", "medium")
            priority_counts[p] = priority_counts.get(p, 0) + 1
            c = t.get("category", "general")
            category_counts[c] = category_counts.get(c, 0) + 1
            if s == "overdue":
                overdue.append(t.get("title", ""))
            elif s == "delayed":
                at_risk.append(t.get("title", ""))

        total = len(tasks)
        completed = status_counts.get("completed", 0)
        stats = {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "by_category": category_counts,
            "completion_rate_pct": round(completed / total * 100, 1),
            "overdue_tasks": overdue,
            "at_risk_tasks": at_risk,
        }

        analysis = self.invoke(
            "Analyse the task progress data. Provide: "
            "1) Overall health (Good/Fair/Critical), "
            "2) Top 3 risk items needing immediate action, "
            "3) Staff who need follow-up, "
            "4) Recommendations to improve completion rate.",
            context=json.dumps(stats, indent=2),
        )
        return {"analysis": analysis, "stats": stats, "risk_items": overdue + at_risk}

    def staff_status_report(self, staff_name: str, tasks: list) -> str:
        return self.invoke(
            f"Generate a concise task status report for '{staff_name}'. "
            "Include: completed count, pending, overdue, and overall performance rating.",
            context=json.dumps(tasks, indent=2),
        )

    def category_breakdown(self, tasks: list, category: str) -> str:
        filtered = [t for t in tasks if t.get("category", "").lower() == category.lower()]
        return self.invoke(
            f"Analyse tasks in the '{category}' category. "
            "Highlight completion rate, overdue items, and key observations.",
            context=json.dumps(filtered, indent=2),
        )

    def department_health_score(self, tasks: list) -> dict:
        total = len(tasks) or 1
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        overdue = sum(1 for t in tasks if t.get("status") == "overdue")
        score = round(max(0, min(100, (completed / total * 60) - (overdue / total * 40) + 40)), 1)
        return {
            "score": score,
            "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "completed_pct": round(completed / total * 100, 1),
            "overdue_pct": round(overdue / total * 100, 1),
        }
