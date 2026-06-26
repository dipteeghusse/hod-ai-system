"""Meeting Manager Agent — generic meeting types, agenda generation, MoM."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class MeetingManagerAgent(BaseAgent):
    name = "meeting_manager"
    description = "Manages meeting scheduling, agenda, minutes, and action item tracking"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Meeting Management agent.\n"
            "Generate professional meeting agendas, record Minutes of Meeting (MoM), "
            "extract action items, and track follow-ups.\n\n"
            "Meeting types you may encounter: department, faculty, committee, review, "
            "accreditation, board, emergency — or any type the user specifies.\n"
            "Always structure agendas with time allocations. "
            "Extract action items as specific, owner-assigned, deadline-bound tasks.\n"
            "Adapt language and formality to the institution and meeting type provided."
        )

    @traceable(name="meeting_manager_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Context:\n{context}\n\nRequest:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def generate_agenda(self, meeting_title: str, meeting_type: str,
                        topics: list = [], pending_action_items: list = []) -> str:
        """topics and pending_action_items are user-supplied — no fixed structure assumed."""
        ctx = {
            "meeting_title": meeting_title,
            "meeting_type": meeting_type,
            "topics_to_cover": topics,
            "pending_action_items_from_last_meeting": pending_action_items,
        }
        return self.invoke(
            f"Generate a formal meeting agenda for '{meeting_title}' ({meeting_type} meeting). "
            "Include: Welcome, Review of previous MoM action items, main agenda items with "
            "time slots, AOB (Any Other Business), and Next Meeting date placeholder. "
            f"Format professionally for {settings.INSTITUTION}.",
            context=json.dumps(ctx, indent=2),
        )

    def generate_mom(self, meeting_title: str, date: str, attendees: list,
                     agenda: str, discussion_notes: str) -> str:
        """discussion_notes is free-form text supplied by the user."""
        ctx = (
            f"Meeting: {meeting_title}\n"
            f"Date: {date}\n"
            f"Attendees: {', '.join(attendees)}\n"
            f"Agenda:\n{agenda}\n"
            f"Discussion Notes:\n{discussion_notes}"
        )
        return self.invoke(
            "Generate a formal Minutes of Meeting (MoM) document. "
            "Include: decisions made, action items (owner + deadline), and next meeting details. "
            f"Format as an official {settings.INSTITUTION} department document.",
            context=ctx,
        )

    def extract_action_items(self, mom_text: str) -> list:
        raw = self.invoke(
            "Extract all action items from this MoM text as a JSON list. "
            "Each item: {action, owner_name, deadline, priority}. Return only the JSON array.",
            context=mom_text,
        )
        try:
            s, e = raw.find("["), raw.rfind("]") + 1
            if s >= 0 and e > s:
                return json.loads(raw[s:e])
        except Exception:
            pass
        return []

    def schedule_suggestion(self, meeting_type: str, purpose: str,
                            attendee_count: int, constraints: str = "") -> str:
        return self.invoke(
            f"Suggest optimal time slots for a {meeting_type} meeting "
            f"(purpose: {purpose}) with {attendee_count} attendees. "
            f"Constraints: {constraints or 'none specified'}. "
            "Consider academic workload norms and avoid exam/assessment periods.",
        )
