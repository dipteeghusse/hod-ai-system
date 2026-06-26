from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from config import settings


# ── Enums ──────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    OVERDUE = "overdue"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserRole(str, Enum):
    HOD = "hod"
    FACULTY = "faculty"
    LAB_ASSISTANT = "lab_assistant"
    OFFICE_STAFF = "office_staff"
    STUDENT = "student"


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    HOD_ASSISTANT = "hod_assistant"
    TASK_PLANNER = "task_planner"
    TASK_ALLOCATOR = "task_allocator"
    PROGRESS_TRACKER = "progress_tracker"
    REMINDER = "reminder"
    MEETING_MANAGER = "meeting_manager"
    EMAIL_INTELLIGENCE = "email_intelligence"
    ACADEMIC_CALENDAR = "academic_calendar"
    FACULTY_PERFORMANCE = "faculty_performance"
    NBA_COMPLIANCE = "nba_compliance"
    REPORT_GENERATOR = "report_generator"


# ── Auth ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.FACULTY
    department: str = "CSE (AI & ML)"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Tasks ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str
    assigned_to_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime
    category: str = "general"   # any value from TASK_CATEGORIES in .env
    subject: Optional[str] = None  # any course/subject name — free text
    tags: List[str] = []
    attachments: List[str] = []

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = settings.task_categories_list
        if v and v not in allowed:
            # Accept unknown categories gracefully — just normalise to lowercase
            return v.lower().strip()
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    progress_percentage: Optional[int] = None
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime
    assigned_to_id: Optional[int]
    assigned_to_name: Optional[str]
    created_by_id: int
    category: str
    tags: List[str]
    progress_percentage: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Meetings ───────────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    description: str
    scheduled_at: datetime
    duration_minutes: int = 60
    location: str = "Department Conference Room"
    meeting_type: str = "department"
    agenda_items: List[str] = []
    attendee_ids: List[int] = []


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: str
    scheduled_at: datetime
    duration_minutes: int
    location: str
    status: MeetingStatus
    agenda_items: List[str]
    minutes: Optional[str]
    action_items: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Faculty ────────────────────────────────────────────────────────────────────

class FacultyProfile(BaseModel):
    id: int
    name: str
    email: str
    designation: str
    specialization: List[str]
    publications_count: int
    fdp_count: int
    ongoing_tasks: int
    completed_tasks: int
    performance_score: float

    class Config:
        from_attributes = True


# ── AI Agent ───────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    query: str
    agent_type: AgentType = AgentType.HOD_ASSISTANT
    context: Dict[str, Any] = {}
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    agent_type: AgentType
    response: str
    actions_taken: List[str] = []
    tasks_created: List[int] = []
    data: Dict[str, Any] = {}
    session_id: Optional[str] = None
    trace_url: Optional[str] = None


# ── Reports ────────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: str  # weekly | monthly | semester | nba | iqac
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = "pdf"  # pdf | word | excel


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    upcoming_meetings: int
    faculty_count: int
    today_deadlines: int
    completion_rate: float
    task_by_priority: Dict[str, int]
    recent_activities: List[Dict[str, Any]]
