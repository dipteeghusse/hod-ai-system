# HOD AI System — MITAOE CSE (AI & ML)

AI-powered HoD Assistant with LangGraph multi-agent orchestration, Groq LLM, LangSmith tracing, and RAG knowledge base.

## Architecture

```
Frontend (Next.js)  →  Backend (FastAPI)  →  LangGraph Orchestrator
                                          →  Router Node → RAG Node → Agent Dispatch
                                                              ↓
                                          Agents: HoD Assistant | Task Planner | Allocator
                                                  Progress Tracker | Meeting Manager
                                                  Email Intelligence | NBA/NAAC | Reports
                                                              ↓
                                                    Groq LLM (llama-3.3-70b)
                                                    LangSmith Tracing
                                                    FAISS RAG Vector Store
```

## Quick Start

### 1. Get API Keys
- **Groq**: https://console.groq.com → Create API Key (free)
- **LangSmith**: https://smith.langchain.com → Settings → API Keys (free)

### 2. Backend Setup
```bash
cd backend
cp .env.example .env
# Edit .env and add GROQ_API_KEY and LANGCHAIN_API_KEY
chmod +x start.sh && ./start.sh
```

### 3. Frontend Setup
```bash
cd frontend
chmod +x start.sh && ./start.sh
```

### 4. Open Browser
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **LangSmith Traces**: https://smith.langchain.com

## Login Credentials (Demo)
| Role | Email | Password |
|------|-------|----------|
| HoD | hodaiml_AI@mitaoe.ac.in | hod@123 |
| Faculty | priya.sharma@mitaoe.ac.in | faculty@123 |
| Faculty | rahul.verma@mitaoe.ac.in | faculty@123 |

## Agents

| Agent | Trigger Keywords |
|-------|-----------------|
| HoD Assistant | priorities, briefing, today, help, plan |
| Task Planner | create plan, weekly plan, circular, schedule |
| Task Allocator | assign, workload, distribute, committee |
| Progress Tracker | status, progress, overdue, completion |
| Meeting Manager | agenda, minutes, MoM, meeting |
| Email Intelligence | email, summarize, draft reply |
| NBA/NAAC Agent | NBA, NAAC, compliance, CO-PO, SAR, audit |
| Report Generator | generate report, weekly report, IQAC |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (llama-3.3-70b-versatile) |
| Agent Framework | LangGraph 0.2 |
| Tracing | LangSmith |
| RAG | FAISS + HuggingFace Embeddings |
| Backend | FastAPI + SQLAlchemy (async) |
| Frontend | Next.js 14 + Tailwind CSS |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose) |

## Project Structure

```
hod-ai-system/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings from .env
│   ├── agents/                    # 8 specialized AI agents
│   │   ├── hod_assistant_agent.py
│   │   ├── task_planner_agent.py
│   │   ├── task_allocation_agent.py
│   │   ├── progress_tracker_agent.py
│   │   ├── meeting_manager_agent.py
│   │   ├── email_intelligence_agent.py
│   │   ├── nba_compliance_agent.py
│   │   └── report_generator_agent.py
│   ├── graph/
│   │   ├── orchestrator.py        # LangGraph workflow
│   │   └── state.py               # Shared agent state
│   ├── rag/
│   │   └── retriever.py           # FAISS + embeddings RAG
│   ├── database/db.py             # SQLAlchemy models + seeding
│   ├── models/schemas.py          # Pydantic schemas
│   └── api/routes.py              # All API endpoints
└── frontend/
    ├── app/
    │   ├── login/page.tsx
    │   ├── dashboard/page.tsx      # Stats + AI briefing
    │   ├── tasks/page.tsx          # Task management
    │   ├── faculty/page.tsx        # Faculty overview
    │   ├── meetings/page.tsx       # Scheduling + AI agenda
    │   ├── chat/page.tsx           # Multi-agent chat UI
    │   ├── reports/page.tsx        # Report generation
    │   └── compliance/page.tsx     # NBA/NAAC tracking
    ├── components/Shared/          # Sidebar, Header, AppShell
    └── lib/                        # API client + Zustand store
```
