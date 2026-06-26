"""Email Intelligence Agent — generic email analysis, no hardcoded subjects or senders."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class EmailIntelligenceAgent(BaseAgent):
    name = "email_intelligence"
    description = "Analyzes emails, extracts tasks, detects priority, and drafts replies"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Email Intelligence agent for the HoD's inbox.\n"
            "You read and summarise emails, detect priority, extract action items and deadlines, "
            "and draft professional reply templates.\n\n"
            "Email categories you may encounter: university circular, meeting invite, "
            "deadline notice, report request, accreditation, student matter, faculty matter, "
            "vendor, government, or any other — classify based on actual email content.\n"
            "Never assume a fixed set of senders or subject lines."
        )

    @traceable(name="email_intelligence_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Email Content:\n{context}\n\nRequest:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def analyze(self, subject: str, sender: str, body: str) -> dict:
        email_text = f"From: {sender}\nSubject: {subject}\n\nBody:\n{body}"
        raw = self.invoke(
            "Analyse this email and return a JSON object:\n"
            "{\n"
            '  "priority": "critical|high|medium|low",\n'
            '  "category": "<detected category>",\n'
            '  "summary": "<2-3 sentence summary>",\n'
            '  "action_items": [{"action": "...", "deadline": "...", "assignee_role": "..."}],\n'
            '  "requires_reply": true|false,\n'
            '  "reply_tone": "formal|urgent|routine",\n'
            '  "suggested_tasks": ["<task title>", ...]\n'
            "}",
            context=email_text,
        )
        try:
            s, e = raw.find("{"), raw.rfind("}") + 1
            if s >= 0 and e > s:
                return json.loads(raw[s:e])
        except Exception:
            pass
        return {"priority": "medium", "summary": raw, "action_items": [], "requires_reply": False}

    def draft_reply(self, subject: str, body: str, reply_intent: str) -> str:
        """
        reply_intent: free-form string — e.g. "accept and confirm date",
                      "decline politely", "request extension by 1 week", etc.
        """
        return self.invoke(
            f"Draft a professional reply email.\n"
            f"Intent: {reply_intent}\n"
            f"Use formal academic institution language. "
            f"Include proper salutation and HoD signature for {settings.DEPARTMENT}, "
            f"{settings.INSTITUTION}.",
            context=f"Original Subject: {subject}\n\nOriginal Email:\n{body}",
        )

    def batch_summarize(self, emails: list) -> str:
        """
        emails: list of {sender, subject, body} — any content, any sender.
        """
        email_list = "\n\n---\n\n".join(
            f"Email {i+1}:\nFrom: {e.get('sender','')}\n"
            f"Subject: {e.get('subject','')}\n"
            f"{e.get('body','')[:400]}..."
            for i, e in enumerate(emails[:15])
        )
        return self.invoke(
            "Provide a priority-sorted inbox digest. "
            "Group as: ACTION REQUIRED TODAY | THIS WEEK | FOR INFORMATION ONLY. "
            "For each email: one-line summary and suggested action.",
            context=email_list,
        )
