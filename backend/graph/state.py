"""LangGraph state definitions for the HOD multi-agent system."""

from typing import TypedDict, Annotated, List, Optional, Any
from operator import add
import operator


class AgentState(TypedDict):
    """Shared state passed between all agents in the graph."""
    # Input
    query: str
    user_id: int
    user_role: str
    session_id: str
    context: dict

    # Routing
    active_agent: str
    agent_history: Annotated[List[str], add]

    # Conversation
    messages: Annotated[List[dict], add]
    rag_context: str

    # Outputs
    response: str
    actions_taken: Annotated[List[str], add]
    tasks_created: List[int]
    data: dict

    # Agent-specific state
    task_plan: Optional[List[dict]]
    assigned_tasks: Optional[List[dict]]
    meeting_agenda: Optional[str]
    report_data: Optional[dict]
    email_summary: Optional[dict]

    # Control flow
    requires_human_approval: bool
    is_complete: bool
    error: Optional[str]
