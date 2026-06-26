"""Progress Tracker Agent — monitors task completion, flags delays and risks."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


class ProgressTrackerAgent(BaseAgent):
    name = "progress_tracker"
    description = "Tracks task progress, identifies delays, and generates status reports"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Progress Tracking agent. You monitor all departmental tasks, "
            "identify delays and risks, compute completion rates, and provide actionable insights. "
            "You generate concise status reports for the HoD with risk alerts and recommendations."
        )

    @traceable(name="progress_tracker_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Task Data:\n{context}\n\nTracking Query: {query}"),
        ]
        return self.llm.invoke(messages).content

    def analyze_progress(self, tasks: list) -> dict:
        total = len(tasks)
        if total == 0:
            return {"analysis": "No tasks to analyze.", "risk_items": [], "stats": {}}

        status_counts = {}
        overdue = []
        at_risk = []

        for t in tasks:
            s = t.get("status", "pending")
            status_counts[s] = status_counts.get(s, 0) + 1
            if s == "overdue":
                overdue.append(t.get("title", ""))
            elif s == "delayed":
                at_risk.append(t.get("title", ""))

        context = json.dumps({
            "total_tasks": total,
            "status_breakdown": status_counts,
            "overdue_tasks": overdue,
            "at_risk_tasks": at_risk,
            "completion_rate": round(status_counts.get("completed", 0) / total * 100, 1),
        }, indent=2)

        analysis = self.invoke(
            "Analyze this department task progress. Provide: "
            "1) Overall health assessment, 2) Risk items needing immediate action, "
            "3) Faculty who need follow-up, 4) Recommendations to improve completion rate.",
            context=context,
        )

        return {
            "analysis": analysis,
            "stats": json.loads(context),
            "risk_items": overdue + at_risk,
        }

    def faculty_status_report(self, faculty_id: int, tasks: list) -> str:
        faculty_tasks = [t for t in tasks if t.get("assigned_to_id") == faculty_id]
        return self.invoke(
            f"Generate a concise status report for faculty ID {faculty_id}. "
            "Include completed count, pending, overdue, and overall performance.",
            context=json.dumps(faculty_tasks, indent=2),
        )

    def department_health_score(self, tasks: list) -> dict:
        total = len(tasks) or 1
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        overdue = sum(1 for t in tasks if t.get("status") == "overdue")
        score = max(0, 100 - (overdue / total * 50) + (completed / total * 50))
        return {
            "score": round(score, 1),
            "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "completed_pct": round(completed / total * 100, 1),
            "overdue_pct": round(overdue / total * 100, 1),
        }
