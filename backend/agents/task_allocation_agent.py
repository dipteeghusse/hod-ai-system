"""Task Allocation Agent — assigns tasks to faculty based on expertise and workload."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


class TaskAllocationAgent(BaseAgent):
    name = "task_allocator"
    description = "Intelligently assigns tasks to faculty based on expertise, workload, and availability"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Task Allocation agent. Your job is to optimally assign departmental tasks "
            "to faculty, lab assistants, office staff, and student coordinators. "
            "Consider: expertise match, current workload, past performance, availability, and deadlines. "
            "Always explain why you assigned a task to a specific person."
        )

    @traceable(name="task_allocation_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Staff Information:\n{context}\n\nAllocation Request: {query}"),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def allocate_tasks(self, tasks: list, faculty_profiles: list) -> dict:
        faculty_str = json.dumps(faculty_profiles, indent=2)
        tasks_str = json.dumps(tasks, indent=2)

        raw = self.invoke(
            f"Allocate these tasks optimally among the faculty. Return a JSON list with "
            f"task_id and assigned_faculty_id for each task, then provide reasoning:\n"
            f"Tasks:\n{tasks_str}",
            context=f"Available Faculty (with workload and expertise):\n{faculty_str}",
        )

        allocations = []
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                allocations = json.loads(raw[start:end])
        except Exception:
            pass

        return {"allocations": allocations, "reasoning": raw}

    def balance_workload(self, faculty_workloads: list) -> str:
        context = json.dumps(faculty_workloads, indent=2)
        return self.invoke(
            "Analyze current faculty workload distribution. Identify overloaded faculty "
            "and suggest task redistribution to balance workload fairly.",
            context=context,
        )

    def suggest_committee_members(self, committee_type: str, faculty_list: list) -> str:
        return self.invoke(
            f"Suggest optimal members for the {committee_type} committee. "
            "Consider expertise, existing committee memberships, and workload.",
            context=json.dumps(faculty_list, indent=2),
        )
