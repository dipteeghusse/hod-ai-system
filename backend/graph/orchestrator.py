"""
LangGraph Orchestrator — routes queries to the right agent and manages multi-step workflows.
Uses a supervisor pattern: Router → Agent → Synthesizer.
"""

from langgraph.graph import StateGraph, END
from langsmith import traceable
from typing import Literal
import json

from graph.state import AgentState
from agents.hod_assistant_agent import HoDAssistantAgent
from agents.task_planner_agent import TaskPlannerAgent
from agents.task_allocation_agent import TaskAllocationAgent
from agents.progress_tracker_agent import ProgressTrackerAgent
from agents.meeting_manager_agent import MeetingManagerAgent
from agents.email_intelligence_agent import EmailIntelligenceAgent
from agents.nba_compliance_agent import NBAComplianceAgent
from agents.report_generator_agent import ReportGeneratorAgent
from agents.followup_agent import FollowUpAgent
from agents.base_agent import get_llm
from rag.retriever import rag_retriever
from langchain_core.messages import SystemMessage, HumanMessage


# ── Agent instances ────────────────────────────────────────────────────────────

_agents = {
    "hod_assistant": HoDAssistantAgent(),
    "followup_agent": FollowUpAgent(),
    "task_planner": TaskPlannerAgent(),
    "task_allocator": TaskAllocationAgent(),
    "progress_tracker": ProgressTrackerAgent(),
    "meeting_manager": MeetingManagerAgent(),
    "email_intelligence": EmailIntelligenceAgent(),
    "nba_compliance": NBAComplianceAgent(),
    "report_generator": ReportGeneratorAgent(),
}

_router_llm = get_llm(temperature=0.1)

ROUTER_SYSTEM = """You are a routing agent for the HOD AI System.
Given a user query, select the single best agent to handle it.

Agents:
- hod_assistant: general HoD questions, daily briefings, priorities, decision support
- followup_agent: follow-up summaries, overdue tasks, who hasn't responded, follow-up messages, stale tasks, at-risk tasks
- task_planner: create task plans, plan from circulars/events, weekly/monthly planning
- task_allocator: assign tasks to faculty, workload balancing, committee suggestions
- progress_tracker: check task progress, department health, status reports
- meeting_manager: schedule meetings, create agenda, generate MoM, track action items
- email_intelligence: summarize emails, draft replies, extract tasks from emails
- nba_compliance: NBA/NAAC compliance, CO-PO attainment, SAR, audit readiness
- report_generator: generate weekly/monthly/semester/IQAC/principal reports

Reply with ONLY the agent name, nothing else."""


# ── Graph Nodes ────────────────────────────────────────────────────────────────

def router_node(state: AgentState) -> AgentState:
    """Determine which specialized agent should handle this query."""
    query = state["query"]

    # Allow explicit agent selection from context
    if state.get("context", {}).get("agent_type"):
        agent_name = state["context"]["agent_type"].replace("_agent", "").replace("task_allocation", "task_allocator")
        if agent_name in _agents:
            return {**state, "active_agent": agent_name, "agent_history": [agent_name]}

    messages = [
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=query),
    ]
    result = _router_llm.invoke(messages)
    chosen = result.content.strip().lower()
    if chosen not in _agents:
        chosen = "hod_assistant"

    return {**state, "active_agent": chosen, "agent_history": [chosen]}


def rag_node(state: AgentState) -> AgentState:
    """Retrieve relevant department knowledge base context."""
    rag_ctx = rag_retriever.retrieve(state["query"], k=4)
    return {**state, "rag_context": rag_ctx}


def dispatch_node(state: AgentState) -> AgentState:
    """Dispatch query to the selected agent."""
    agent_name = state["active_agent"]
    agent = _agents.get(agent_name, _agents["hod_assistant"])

    context = state.get("rag_context", "")
    if state.get("context"):
        context = json.dumps(state["context"]) + "\n\n" + context

    response = agent.invoke(
        query=state["query"],
        context=context,
    )

    return {
        **state,
        "response": response,
        "actions_taken": [f"Agent '{agent_name}' processed query"],
        "is_complete": True,
    }


def error_node(state: AgentState) -> AgentState:
    return {
        **state,
        "response": "I encountered an issue processing your request. Please try again or contact support.",
        "is_complete": True,
        "error": state.get("error", "Unknown error"),
    }


def route_after_router(state: AgentState) -> Literal["rag", "error"]:
    if state.get("error"):
        return "error"
    return "rag"


# ── Build Graph ────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("dispatch", dispatch_node)
    graph.add_node("error", error_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_after_router, {"rag": "rag", "error": "error"})
    graph.add_edge("rag", "dispatch")
    graph.add_edge("dispatch", END)
    graph.add_edge("error", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


@traceable(name="hod_orchestrator")
async def run_agent(
    query: str,
    user_id: int = 1,
    user_role: str = "hod",
    agent_type: str = None,
    context: dict = {},
    session_id: str = "default",
) -> dict:
    graph = get_graph()

    initial_state: AgentState = {
        "query": query,
        "user_id": user_id,
        "user_role": user_role,
        "session_id": session_id,
        "context": {**({"agent_type": agent_type} if agent_type else {}), **context},
        "active_agent": "",
        "agent_history": [],
        "messages": [],
        "rag_context": "",
        "response": "",
        "actions_taken": [],
        "tasks_created": [],
        "data": {},
        "task_plan": None,
        "assigned_tasks": None,
        "meeting_agenda": None,
        "report_data": None,
        "email_summary": None,
        "requires_human_approval": False,
        "is_complete": False,
        "error": None,
    }

    result = graph.invoke(initial_state)

    return {
        "agent_type": result.get("active_agent", "hod_assistant"),
        "response": result.get("response", ""),
        "actions_taken": result.get("actions_taken", []),
        "tasks_created": result.get("tasks_created", []),
        "data": result.get("data", {}),
        "session_id": session_id,
    }
