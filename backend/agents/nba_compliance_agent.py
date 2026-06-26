"""NBA/NAAC Compliance Agent — tracks SAR, CO-PO attainment, documentation status."""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from agents.base_agent import BaseAgent


NBA_CRITERIA = {
    "1": "Vision, Mission, Program Educational Objectives",
    "2": "Program Outcomes and Course Outcomes",
    "3": "Program Curriculum and Teaching-Learning Processes",
    "4": "Students' Performance",
    "5": "Faculty Information and Contributions",
    "6": "Facilities and Technical Support",
    "7": "Continuous Improvement",
    "8": "First Year Academics",
}

NAAC_CRITERIA = {
    "1": "Curricular Aspects",
    "2": "Teaching-Learning and Evaluation",
    "3": "Research, Innovations and Extension",
    "4": "Infrastructure and Learning Resources",
    "5": "Student Support and Progression",
    "6": "Governance, Leadership and Management",
    "7": "Institutional Values and Best Practices",
}


class NBAComplianceAgent(BaseAgent):
    name = "nba_compliance"
    description = "Tracks NBA/NAAC compliance, SAR preparation, and accreditation readiness"

    def __init__(self):
        super().__init__()
        self._system = self._system_prompt(
            "You are the NBA/NAAC Compliance agent for the CSE-AIML department. "
            "You track accreditation documentation, CO-PO attainment, SAR preparation progress, "
            "and ensure all evidence is collected and ready for audit. "
            "You know NBA criteria (1-8) and NAAC criteria (1-7) deeply and can generate "
            "compliance checklists, gap analyses, and audit readiness reports."
        )

    @traceable(name="nba_compliance_agent")
    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        messages = [
            SystemMessage(content=self._system),
            HumanMessage(content=f"Compliance Context:\n{context}\n\nQuery: {query}"),
        ]
        return self.llm.invoke(messages).content

    def generate_compliance_checklist(self, accreditation_type: str = "NBA") -> dict:
        criteria = NBA_CRITERIA if accreditation_type == "NBA" else NAAC_CRITERIA
        context = json.dumps(criteria, indent=2)

        checklist_text = self.invoke(
            f"Generate a detailed {accreditation_type} compliance checklist for CSE-AIML department. "
            "For each criterion, list specific documents required, evidence types, "
            "responsible faculty, and completion status format. "
            "Return as a structured checklist with checkboxes.",
            context=context,
        )
        return {
            "type": accreditation_type,
            "criteria": criteria,
            "checklist": checklist_text,
        }

    def co_po_attainment_analysis(self, course_name: str, scores_data: list) -> str:
        context = f"Course: {course_name}\nStudent Scores:\n{json.dumps(scores_data, indent=2)}"
        return self.invoke(
            "Calculate CO attainment levels. Target: ≥60% students scoring ≥60% per CO. "
            "Provide attainment table, overall course PO mapping, and gap analysis. "
            "Format for NBA SAR submission.",
            context=context,
        )

    def audit_readiness_report(self, documentation_status: dict) -> str:
        return self.invoke(
            "Generate an audit readiness report. Identify: "
            "1) Ready documents, 2) Documents needing update, 3) Missing documents, "
            "4) Critical gaps that must be addressed before audit, "
            "5) Recommended action plan with deadlines.",
            context=json.dumps(documentation_status, indent=2),
        )

    def sar_section_draft(self, criterion_number: str, evidence_data: dict) -> str:
        return self.invoke(
            f"Draft the SAR narrative for NBA Criterion {criterion_number}: "
            f"{NBA_CRITERIA.get(criterion_number, '')}. "
            "Write in formal accreditation language with evidence citations. "
            "Highlight strengths and ongoing improvements.",
            context=json.dumps(evidence_data, indent=2),
        )
