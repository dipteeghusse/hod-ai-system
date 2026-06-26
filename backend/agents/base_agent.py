"""Base agent class shared by all HOD system agents."""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langsmith import traceable
from typing import Any, Optional
from config import settings


def get_llm(temperature: float = 0.3, max_tokens: int = 2048) -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


class BaseAgent:
    name: str = "base_agent"
    description: str = "Base HOD system agent"

    def __init__(self):
        self.llm = get_llm()
        self.department = settings.DEPARTMENT
        self.institution = settings.INSTITUTION

    def _system_prompt(self, role_description: str) -> str:
        return f"""You are an AI agent for {self.institution} {self.department} department.
Your role: {role_description}

Department: {self.department}
Institution: {self.institution}
Academic Year: {settings.ACADEMIC_YEAR}

Always:
- Be concise and actionable
- Reference MITAOE/CSE-AIML context where relevant
- Structure responses clearly with bullet points or numbered lists
- Flag urgent items prominently
- Suggest next steps

Format your response in clear sections when appropriate."""

    def invoke(self, query: str, context: str = "", history: list = []) -> str:
        raise NotImplementedError
