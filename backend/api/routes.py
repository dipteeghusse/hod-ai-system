"""FastAPI routes for the HOD AI System."""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import uuid
import json

from database.db import get_db, User, Task, Meeting, FacultyActivity, AgentLog
from models.schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingCreate, MeetingResponse,
    AgentRequest, AgentResponse,
    DashboardStats, ReportRequest,
)
from graph.orchestrator import run_agent
from config import settings

router = APIRouter()
pwd_ctx = CryptContext(schemes=["bcrypt"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Public Config Endpoint ────────────────────────────────────────────────────

@router.get("/config")
async def get_config():
    """
    Returns all dynamic department configuration values.
    Frontend uses this to populate dropdowns (categories, subjects, designations, etc.)
    without hardcoding anything.
    """
    return {
        "institution": settings.INSTITUTION,
        "department": settings.DEPARTMENT,
        "program_level": settings.PROGRAM_LEVEL,
        "academic_year": settings.ACADEMIC_YEAR,
        "accreditation_body": settings.ACCREDITATION_BODY,
        "task_categories": settings.task_categories_list,
        "subjects": settings.subjects_list,
        "designations": settings.designations_list,
        "activity_types": settings.activity_types_list,
        "accreditation_criteria": settings.accreditation_criteria_dict,
    }


# ── Auth Helpers ───────────────────────────────────────────────────────────────

def create_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(token: str = Depends(oauth2), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Auth Routes ────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=Token)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=data.name, email=data.email,
        hashed_password=pwd_ctx.hash(data.password),
        role=data.role, department=data.department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_token(user.id, user.role)
    return {"access_token": token, "user": UserResponse.model_validate(user)}


@router.post("/auth/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_ctx.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id, user.role)
    return {"access_token": token, "user": UserResponse.model_validate(user)}


@router.get("/auth/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59)

    task_q = select(Task)
    if current_user.role != "hod":
        task_q = task_q.where(Task.assigned_to_id == current_user.id)

    tasks = (await db.execute(task_q)).scalars().all()

    status_counts = {}
    for t in tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1

    priority_counts = {}
    for t in tasks:
        priority_counts[t.priority] = priority_counts.get(t.priority, 0) + 1

    meetings_q = select(func.count(Meeting.id)).where(
        and_(Meeting.scheduled_at >= today_start, Meeting.scheduled_at <= today_end)
    )
    meeting_count = (await db.execute(meetings_q)).scalar() or 0

    faculty_count = (await db.execute(select(func.count(User.id)).where(User.role == "faculty"))).scalar() or 0

    today_deadlines = sum(1 for t in tasks if today_start <= t.due_date <= today_end)
    total = len(tasks) or 1
    completed = status_counts.get("completed", 0)

    recent = await db.execute(
        select(AgentLog).order_by(AgentLog.created_at.desc()).limit(5)
    )
    recent_logs = [{"agent": r.agent_type, "query": r.query[:60], "time": r.created_at.isoformat()}
                   for r in recent.scalars().all()]

    return DashboardStats(
        total_tasks=len(tasks),
        pending_tasks=status_counts.get("pending", 0),
        in_progress_tasks=status_counts.get("in_progress", 0),
        completed_tasks=completed,
        overdue_tasks=status_counts.get("overdue", 0),
        upcoming_meetings=meeting_count,
        faculty_count=faculty_count,
        today_deadlines=today_deadlines,
        completion_rate=round(completed / total * 100, 1),
        task_by_priority=priority_counts,
        recent_activities=recent_logs,
    )


# ── Task Routes ────────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=List[dict])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Task)
    if current_user.role != "hod":
        q = q.where(Task.assigned_to_id == current_user.id)
    if status:
        q = q.where(Task.status == status)
    if priority:
        q = q.where(Task.priority == priority)
    if assigned_to:
        q = q.where(Task.assigned_to_id == assigned_to)
    q = q.order_by(Task.due_date.asc())

    tasks = (await db.execute(q)).scalars().all()
    result = []
    for t in tasks:
        td = {
            "id": t.id, "title": t.title, "description": t.description,
            "status": t.status, "priority": t.priority, "due_date": t.due_date.isoformat(),
            "category": t.category, "tags": t.tags or [], "progress_percentage": t.progress_percentage,
            "assigned_to_id": t.assigned_to_id, "created_at": t.created_at.isoformat(),
        }
        if t.assignee:
            td["assigned_to_name"] = t.assignee.name
        result.append(td)
    return result


@router.post("/tasks", response_model=dict, status_code=201)
async def create_task(data: TaskCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = Task(
        title=data.title, description=data.description,
        assigned_to_id=data.assigned_to_id,
        priority=data.priority, due_date=data.due_date,
        category=data.category, tags=data.tags,
        created_by_id=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status, "message": "Task created"}


@router.patch("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: int, data: TaskUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()
    await db.commit()
    return {"id": task.id, "status": task.status, "message": "Task updated"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "hod":
        raise HTTPException(403, "Only HoD can delete tasks")
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}


# ── Meeting Routes ─────────────────────────────────────────────────────────────

@router.get("/meetings", response_model=List[dict])
async def get_meetings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Meeting).order_by(Meeting.scheduled_at.desc())
    meetings = (await db.execute(q)).scalars().all()
    return [
        {
            "id": m.id, "title": m.title, "description": m.description,
            "scheduled_at": m.scheduled_at.isoformat(), "duration_minutes": m.duration_minutes,
            "location": m.location, "status": m.status, "meeting_type": m.meeting_type,
            "agenda_items": m.agenda_items or [], "action_items": m.action_items or [],
        }
        for m in meetings
    ]


@router.post("/meetings", response_model=dict, status_code=201)
async def create_meeting(data: MeetingCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    meeting = Meeting(
        title=data.title, description=data.description,
        scheduled_at=data.scheduled_at, duration_minutes=data.duration_minutes,
        location=data.location, meeting_type=data.meeting_type,
        agenda_items=data.agenda_items, attendee_ids=data.attendee_ids,
        created_by_id=current_user.id,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return {"id": meeting.id, "title": meeting.title, "message": "Meeting scheduled"}


@router.post("/meetings/{meeting_id}/generate-agenda")
async def generate_agenda(meeting_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    agenda_result = await run_agent(
        query=f"Generate a formal agenda for meeting: '{meeting.title}' (type: {meeting.meeting_type}). "
              f"Scheduled for: {meeting.scheduled_at.strftime('%A %B %d, %Y at %I:%M %p')}",
        user_id=current_user.id, user_role=current_user.role,
        agent_type="meeting_manager",
    )
    meeting.agenda_items = [agenda_result["response"]]
    await db.commit()
    return {"agenda": agenda_result["response"]}


# ── Faculty Routes ─────────────────────────────────────────────────────────────

@router.get("/faculty", response_model=List[dict])
async def get_faculty(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.role == "faculty", User.is_active == True))
    faculty = result.scalars().all()
    faculty_list = []
    for f in faculty:
        tasks = (await db.execute(select(Task).where(Task.assigned_to_id == f.id))).scalars().all()
        completed = sum(1 for t in tasks if t.status == "completed")
        faculty_list.append({
            "id": f.id, "name": f.name, "email": f.email,
            "designation": f.designation or "Faculty",
            "specialization": f.specialization or [],
            "total_tasks": len(tasks),
            "completed_tasks": completed,
            "pending_tasks": len(tasks) - completed,
            "performance_score": round(completed / max(len(tasks), 1) * 100, 1),
        })
    return faculty_list


# ── AI Agent Routes ────────────────────────────────────────────────────────────

@router.post("/agent/chat", response_model=dict)
async def agent_chat(request: AgentRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())

    result = await run_agent(
        query=request.query,
        user_id=current_user.id,
        user_role=current_user.role,
        agent_type=request.agent_type.value if request.agent_type else None,
        context=request.context,
        session_id=session_id,
    )

    log = AgentLog(
        agent_type=result["agent_type"],
        query=request.query,
        response=result["response"],
        actions_taken=result.get("actions_taken", []),
        session_id=session_id,
        user_id=current_user.id,
    )
    db.add(log)
    await db.commit()

    return {**result, "session_id": session_id}


@router.get("/agent/history")
async def agent_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(AgentLog).where(AgentLog.user_id == current_user.id).order_by(AgentLog.created_at.desc()).limit(50)
    logs = (await db.execute(q)).scalars().all()
    return [
        {"id": l.id, "agent": l.agent_type, "query": l.query, "response": l.response[:200],
         "session_id": l.session_id, "created_at": l.created_at.isoformat()}
        for l in logs
    ]


# ── Report Routes ──────────────────────────────────────────────────────────────

@router.post("/reports/generate")
async def generate_report(request: ReportRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != "hod":
        raise HTTPException(403, "Only HoD can generate reports")

    tasks = (await db.execute(select(Task))).scalars().all()
    faculty = (await db.execute(select(User).where(User.role == "faculty"))).scalars().all()

    context = {
        "report_type": request.report_type,
        "total_tasks": len(tasks),
        "completed": sum(1 for t in tasks if t.status == "completed"),
        "pending": sum(1 for t in tasks if t.status == "pending"),
        "overdue": sum(1 for t in tasks if t.status == "overdue"),
        "faculty_count": len(faculty),
        "department": settings.DEPARTMENT,
        "institution": settings.INSTITUTION,
        "academic_year": settings.ACADEMIC_YEAR,
    }

    result = await run_agent(
        query=f"Generate a {request.report_type} report for the department",
        user_id=current_user.id, user_role=current_user.role,
        agent_type="report_generator",
        context=context,
    )
    return {"report": result["response"], "type": request.report_type}


# ── WebSocket Chat ─────────────────────────────────────────────────────────────

active_connections: dict = {}


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "")
            agent_type = data.get("agent_type")

            await websocket.send_json({"type": "thinking", "message": "Processing your request..."})

            result = await run_agent(
                query=query, user_id=data.get("user_id", 1),
                user_role=data.get("user_role", "hod"),
                agent_type=agent_type, session_id=session_id,
            )

            await websocket.send_json({
                "type": "response",
                "agent": result["agent_type"],
                "response": result["response"],
                "actions": result.get("actions_taken", []),
            })
    except WebSocketDisconnect:
        active_connections.pop(session_id, None)
