from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Float, Enum as SAEnum
from datetime import datetime
from typing import Optional, List
import enum

from config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── ORM Models ─────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(50), default="faculty")
    department: Mapped[str] = mapped_column(String(200), default="CSE (AI & ML)")
    designation: Mapped[Optional[str]] = mapped_column(String(200))
    specialization: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_tasks: Mapped[List["Task"]] = relationship("Task", foreign_keys="Task.assigned_to_id", back_populates="assignee")
    created_tasks: Mapped[List["Task"]] = relationship("Task", foreign_keys="Task.created_by_id", back_populates="creator")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    category: Mapped[str] = mapped_column(String(100), default="general")
    due_date: Mapped[datetime] = mapped_column(DateTime)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    attachments: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tasks")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    location: Mapped[str] = mapped_column(String(300), default="Department Conference Room")
    meeting_type: Mapped[str] = mapped_column(String(100), default="department")
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    agenda_items: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    attendee_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    minutes: Mapped[Optional[str]] = mapped_column(Text)
    action_items: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FacultyActivity(Base):
    __tablename__ = "faculty_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    activity_type: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    date: Mapped[datetime] = mapped_column(DateTime)
    api_points: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(100))
    query: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    actions_taken: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    session_id: Mapped[Optional[str]] = mapped_column(String(200))
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    trace_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FollowUpLog(Base):
    """Persists each follow-up summary run so the HoD can review history."""
    __tablename__ = "followup_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generated_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Counts snapshot
    overdue_count: Mapped[int] = mapped_column(Integer, default=0)
    at_risk_count: Mapped[int] = mapped_column(Integer, default=0)
    stale_count: Mapped[int] = mapped_column(Integer, default=0)
    no_response_count: Mapped[int] = mapped_column(Integer, default=0)
    # Full AI narrative
    narrative: Mapped[str] = mapped_column(Text)
    # Serialised classification data
    detail: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_demo_data()


async def _seed_demo_data():
    """Seed initial HOD and faculty accounts for demo."""
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"])

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == settings.HOD_EMAIL))
        if result.scalar_one_or_none():
            return

        hod = User(
            name="Dr. HoD CSE-AIML",
            email=settings.HOD_EMAIL,
            hashed_password=pwd.hash("hod@123"),
            role="hod",
            department="CSE (AI & ML)",
            designation="Head of Department",
            specialization=["Artificial Intelligence", "Machine Learning"],
        )
        db.add(hod)

        faculty_seed = [
            ("Dr. Priya Sharma", "priya.sharma@mitaoe.ac.in", "Associate Professor", ["Deep Learning", "NLP"]),
            ("Dr. Rahul Verma", "rahul.verma@mitaoe.ac.in", "Assistant Professor", ["Computer Vision", "GenAI"]),
            ("Prof. Sneha Patil", "sneha.patil@mitaoe.ac.in", "Assistant Professor", ["ML", "Data Science"]),
            ("Dr. Amit Kumar", "amit.kumar@mitaoe.ac.in", "Associate Professor", ["Reinforcement Learning", "Robotics"]),
        ]
        for name, email, desig, spec in faculty_seed:
            db.add(User(
                name=name, email=email,
                hashed_password=pwd.hash("faculty@123"),
                role="faculty", department="CSE (AI & ML)",
                designation=desig, specialization=spec,
            ))

        await db.commit()
