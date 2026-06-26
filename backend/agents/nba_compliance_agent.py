"""
NBA/NAAC Compliance Agent — fully generic.
Accreditation body, criteria labels, and course names all come from config/user input.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent
from config import settings


class NBAComplianceAgent(BaseAgent):
    name = "nba_compliance"
    description = "Tracks accreditation compliance, CO-PO attainment, SAR drafting, audit readiness"

    def __init__(self):
        super().__init__()
        criteria_text = "\n".join(
            f"  Criterion {k}: {v}"
            for k, v in settings.accreditation_criteria_dict.items()
        )
        self._system = self._system_prompt(
            f"You are the Accreditation Compliance agent for {settings.ACCREDITATION_BODY}.\n\n"
            f"Configured criteria:\n{criteria_text}\n\n"
            "You help with: compliance checklists, CO-PO attainment calculations, "
            "SAR narrative drafting, gap analysis, and audit readiness reports.\n\n"
            "Important: The course names, CO labels, and evidence details are always "
            "supplied by the user — never assume fixed subject names."
        )

    @traceable(name="nba_compliance_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Compliance Context:\n{context}\n\nQuery:\n{query}"),
        ]
        return self.llm.invoke(messages).content

    def compliance_checklist(self, accreditation_type: str = None) -> str:
        body = accreditation_type or settings.ACCREDITATION_BODY
        criteria = settings.accreditation_criteria_dict
        return self.invoke(
            f"Generate a detailed {body} compliance checklist for the department. "
            "For each criterion list: required documents, evidence types, responsible role, "
            "and a completion-status column. Use the configured criteria.",
            context=json.dumps(criteria, indent=2),
        )

    def co_po_attainment(self, course_name: str, co_scores: dict, target_pct: int = 60) -> str:
        """
        course_name : any subject name supplied by user
        co_scores   : {"CO1": [72, 45, 68, 80], "CO2": [65, 70, 48, 85], ...}
        target_pct  : pass threshold (default 60 — i.e., 60% students score ≥60%)
        """
        return self.invoke(
            f"Calculate CO attainment for course: '{course_name}'.\n"
            f"Target: ≥{target_pct}% of students scoring ≥{target_pct}%.\n"
            "Produce: attainment table per CO, overall PO mapping, gap analysis, "
            f"and a compliance verdict for {settings.ACCREDITATION_BODY} submission.",
            context=f"Student Scores per CO:\n{json.dumps(co_scores, indent=2)}",
        )

    def audit_readiness(self, documentation_status: dict) -> str:
        """
        documentation_status: {criterion_label: {status: ready|pending|missing, notes: str}}
        """
        return self.invoke(
            "Generate an audit readiness report. Categorise documents as: "
            "Ready | Needs Update | Missing. Identify critical gaps and provide "
            "an action plan with suggested deadlines.",
            context=json.dumps(documentation_status, indent=2),
        )

    def draft_sar_section(self, criterion_key: str, evidence_data: dict) -> str:
        """
        criterion_key  : matches a key in ACCREDITATION_CRITERIA (e.g. "2")
        evidence_data  : free-form dict of evidence the user provides
        """
        criteria = settings.accreditation_criteria_dict
        label = criteria.get(str(criterion_key), f"Criterion {criterion_key}")
        return self.invoke(
            f"Draft the SAR narrative for Criterion {criterion_key}: '{label}'.\n"
            "Write in formal accreditation language. Cite the evidence provided. "
            "Highlight strengths and describe ongoing improvements.",
            context=json.dumps(evidence_data, indent=2),
        )

    def gap_analysis(self, current_status: dict) -> str:
        return self.invoke(
            f"Perform a {settings.ACCREDITATION_BODY} gap analysis. "
            "Rank gaps by severity (Critical / Major / Minor). "
            "Suggest specific actions and owners for each gap.",
            context=json.dumps(current_status, indent=2),
        )
