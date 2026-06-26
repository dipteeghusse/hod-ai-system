"""Email Intelligence Agent — summarizes, prioritizes, extracts action items, drafts replies."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


class EmailIntelligenceAgent(BaseAgent):
    name = "email_intelligence"
    description = "Analyzes emails, extracts tasks, drafts replies, and prioritizes inbox"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the Email Intelligence agent for the HoD's inbox. "
            "You read and summarize emails, detect priority level, extract actionable items, "
            "identify deadlines, and draft professional reply templates. "
            "You also automatically create tasks from emails that require department action."
        )

    @traceable(name="email_intelligence_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Email Content:\n{context}\n\nRequest: {query}"),
        ]
        return self.llm.invoke(messages).content

    def analyze_email(self, subject: str, sender: str, body: str) -> dict:
        email_text = f"From: {sender}\nSubject: {subject}\n\nBody:\n{body}"

        analysis_prompt = """Analyze this email and return a JSON object with:
{
  "priority": "critical|high|medium|low",
  "category": "university_circular|meeting_invite|deadline_notice|report_request|general",
  "summary": "2-3 sentence summary",
  "action_items": [{"action": "...", "deadline": "...", "assignee": "..."}],
  "requires_reply": true/false,
  "sentiment": "formal|urgent|routine",
  "suggested_tasks": ["task1", "task2"]
}"""

        raw = self.invoke(analysis_prompt, context=email_text)
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except Exception:
            pass
        return {"priority": "medium", "summary": raw, "action_items": [], "requires_reply": False}

    def draft_reply(self, original_subject: str, original_body: str,
                    reply_intent: str) -> str:
        context = f"Original Subject: {original_subject}\n\nOriginal Email:\n{original_body}"
        return self.invoke(
            f"Draft a professional reply email. Intent: {reply_intent}. "
            "Use formal academic institution language appropriate for MITAOE. "
            "Include proper salutation and signature for HoD CSE-AIML.",
            context=context,
        )

    def batch_summarize(self, emails: list) -> str:
        email_list = "\n\n---\n\n".join(
            f"Email {i+1}:\nFrom: {e.get('sender')}\nSubject: {e.get('subject')}\n{e.get('body', '')[:300]}..."
            for i, e in enumerate(emails[:10])
        )
        return self.invoke(
            "Provide a priority-sorted inbox summary. Group by urgency: "
            "CRITICAL (needs action today) | HIGH (this week) | ROUTINE.",
            context=email_list,
        )
