"""Meeting Manager Agent — agenda, minutes, action items, follow-ups."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


class MeetingManagerAgent(BaseAgent):
    name = "meeting_manager"
    description = "Manages meeting scheduling, agenda generation, MoM, and action item tracking"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Meeting Management agent for the CSE-AIML department. "
            "You generate professional meeting agendas, record minutes of meetings (MoM), "
            "extract action items, and track follow-ups. "
            "Always structure agendas with time allocations and output MoM in MITAOE official format."
        )

    @traceable(name="meeting_manager_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Context:\n{context}\n\nRequest: {query}"),
        ]
        return self.llm.invoke(messages).content

    def generate_agenda(self, meeting_title: str, meeting_type: str,
                        pending_tasks: list, previous_action_items: list) -> str:
        context = {
            "meeting_type": meeting_type,
            "pending_departmental_tasks": [t.get("title") for t in pending_tasks[:10]],
            "pending_action_items_from_last_meeting": previous_action_items[:5],
        }
        return self.invoke(
            f"Generate a formal meeting agenda for: '{meeting_title}'. "
            "Include: Welcome, Review of previous MoM, agenda items with time slots, "
            "AOB (Any Other Business), and closing. Format professionally for MITAOE.",
            context=json.dumps(context, indent=2),
        )

    def generate_mom(self, meeting_title: str, attendees: list,
                     agenda: str, discussion_notes: str) -> str:
        context = f"""
Meeting: {meeting_title}
Attendees: {', '.join(attendees)}
Agenda: {agenda}
Discussion Notes: {discussion_notes}
"""
        return self.invoke(
            "Generate a formal Minutes of Meeting (MoM) document. "
            "Extract all decisions made, action items with owners and deadlines, "
            "and format as an official MITAOE department document.",
            context=context,
        )

    def extract_action_items(self, mom_text: str) -> list:
        raw = self.invoke(
            "Extract all action items from this MoM as a JSON list with fields: "
            "action, owner_name, deadline, priority. Return only the JSON array.",
            context=mom_text,
        )
        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return []

    def schedule_suggestion(self, meeting_type: str, attendee_count: int,
                            preferred_time: str) -> str:
        return self.invoke(
            f"Suggest optimal time slots for a {meeting_type} meeting with {attendee_count} attendees. "
            f"Preferred time: {preferred_time}. Consider academic schedule norms.",
        )
