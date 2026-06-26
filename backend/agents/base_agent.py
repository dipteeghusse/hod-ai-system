"""Base agent — all context built from config, nothing hardcoded."""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from config import settings


def get_llm(temperature: float = 0.3, max_tokens: int = 2048) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def dept_context() -> str:
    """Build a concise department context block from config values."""
    return (
        f"Institution: {settings.INSTITUTION}\n"
        f"Department: {settings.DEPARTMENT}\n"
        f"Program: {settings.PROGRAM_LEVEL}\n"
        f"Academic Year: {settings.ACADEMIC_YEAR}\n"
        f"Accreditation Body: {settings.ACCREDITATION_BODY}\n"
        f"Task Categories: {', '.join(settings.task_categories_list)}\n"
        f"Subjects/Courses: {', '.join(settings.subjects_list)}\n"
        f"Faculty Designations: {', '.join(settings.designations_list)}"
    )


class BaseAgent:
    name: str = "base_agent"
    description: str = "Base HOD system agent"

    def __init__(self):
        self.llm = get_llm()

    def _system_prompt(self, role_description: str) -> str:
        return (
            f"You are an AI agent for the {settings.DEPARTMENT} department "
            f"at {settings.INSTITUTION}.\n\n"
            f"Your role: {role_description}\n\n"
            f"Department Context:\n{dept_context()}\n\n"
            "Guidelines:\n"
            "- Be concise and actionable.\n"
            "- Adapt your response to the department's subjects and task categories above.\n"
            "- Do NOT hardcode institution or subject names — use only what is provided in context.\n"
            "- Flag urgent or overdue items clearly.\n"
            "- Structure output with headings or bullet points when helpful.\n"
            "- Suggest next steps at the end of every response."
        )

    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        raise NotImplementedError
