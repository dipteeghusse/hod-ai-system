"""Task Allocation Agent — generic workload-aware assignment for any department."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class TaskAllocationAgent(BaseAgent):
    name = "task_allocator"
    description = "Assigns tasks to staff based on expertise, workload, and availability"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Task Allocation agent. Optimally assign departmental tasks to "
            "faculty, lab assistants, office staff, and student coordinators.\n\n"
            "Consider: expertise match, current workload, past performance, availability, "
            "and deadline urgency. Always explain why each task was assigned to a specific person.\n\n"
            "Staff roles available: faculty, lab_assistant, office_staff, student_coordinator, hod.\n"
            "Do not assume fixed subjects or specialisations — use only what the user provides."
        )

    @traceable(name="task_allocation_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Staff Information:\n{context}\n\nAllocation Request:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def allocate_tasks(self, tasks: list, staff_profiles: list) -> dict:
        """
        tasks: list of dicts — {title, description, priority, category, deadline}
        staff_profiles: list of dicts — {id, name, role, specialization, current_task_count}
        """
        raw = self.invoke(
            "Allocate these tasks optimally. Return a JSON list: "
            "[{task_title, assigned_to_name, assigned_to_id, reason}]. "
            "Then provide a plain-English reasoning summary.\n\n"
            f"Tasks:\n{json.dumps(tasks, indent=2)}",
            context=f"Available Staff:\n{json.dumps(staff_profiles, indent=2)}",
        )
        allocations = []
        try:
            s, e = raw.find("["), raw.rfind("]") + 1
            if s >= 0 and e > s:
                allocations = json.loads(raw[s:e])
        except Exception:
            pass
        return {"allocations": allocations, "reasoning": raw}

    def balance_workload(self, staff_workloads: list) -> str:
        """
        staff_workloads: [{name, role, task_count, overdue_count, specialization}]
        """
        return self.invoke(
            "Analyse the workload distribution below. Identify overloaded staff and "
            "suggest specific task transfers to rebalance fairly.",
            context=json.dumps(staff_workloads, indent=2),
        )

    def suggest_committee(self, committee_name: str, purpose: str, staff_list: list) -> str:
        """Generic committee suggestion — works for any committee name/purpose."""
        return self.invoke(
            f"Suggest members for the '{committee_name}' committee.\n"
            f"Purpose: {purpose}\n"
            "Consider existing committee load, expertise, and availability.",
            context=json.dumps(staff_list, indent=2),
        )
