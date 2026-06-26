from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "hod-ai-system"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hod_system.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # SMTP (outbound — optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # IMAP (inbound — automated email recognition)
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    IMAP_FOLDER: str = "INBOX"
    IMAP_POLL_INTERVAL: int = 300   # seconds between inbox checks
    IMAP_MAX_EMAILS: int = 10       # max unread emails per poll

    # ── Institution (change these in .env to use for any college/dept) ────────
    APP_NAME: str = "HOD AI System"
    HOD_EMAIL: str = "hod@institution.ac.in"
    DEPARTMENT: str = "Computer Science & Engineering"
    INSTITUTION: str = "My Institution"
    ACADEMIC_YEAR: str = "2025-26"
    ACCREDITATION_BODY: str = "NBA"          # NBA | NAAC | ABET | AICTE
    PROGRAM_LEVEL: str = "B.Tech"            # B.Tech | M.Tech | MCA | BCA

    # ── Task categories (comma-separated, fully customisable) ─────────────────
    TASK_CATEGORIES: str = (
        "academic,research,administrative,examination,"
        "accreditation,events,student_activities,laboratory,placement"
    )

    # ── Subject/Course list (comma-separated) — used by planner & compliance ──
    SUBJECTS: str = (
        "Data Structures,Algorithms,Database Management,Operating Systems,"
        "Computer Networks,Software Engineering,Machine Learning,Web Technology"
    )

    # ── Accreditation criteria labels (pipe-separated key:label pairs) ────────
    # Override in .env to match your accreditation body's exact criteria titles
    ACCREDITATION_CRITERIA: str = (
        "1:Vision Mission & PEOs|"
        "2:Program Outcomes & Course Outcomes|"
        "3:Curriculum & Teaching-Learning|"
        "4:Students Performance|"
        "5:Faculty Contributions|"
        "6:Facilities & Technical Support|"
        "7:Continuous Improvement|"
        "8:First Year Academics"
    )

    # ── Faculty designation options (comma-separated) ─────────────────────────
    DESIGNATIONS: str = (
        "Professor,Associate Professor,Assistant Professor,"
        "Senior Assistant Professor,Lab Instructor,Adjunct Faculty"
    )

    # ── Activity types for API/performance scoring ────────────────────────────
    ACTIVITY_TYPES: str = (
        "journal_publication,conference_paper,patent,funded_project,"
        "fdp_attended,fdp_organized,guest_lecture,workshop,certification,"
        "consultancy,phd_guidance,hackathon,industrial_visit"
    )

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # RAG
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_PATH: str = "./rag/vector_store"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def task_categories_list(self) -> List[str]:
        return [c.strip() for c in self.TASK_CATEGORIES.split(",")]

    @property
    def subjects_list(self) -> List[str]:
        return [s.strip() for s in self.SUBJECTS.split(",")]

    @property
    def accreditation_criteria_dict(self) -> dict:
        result = {}
        for pair in self.ACCREDITATION_CRITERIA.split("|"):
            if ":" in pair:
                k, v = pair.split(":", 1)
                result[k.strip()] = v.strip()
        return result

    @property
    def designations_list(self) -> List[str]:
        return [d.strip() for d in self.DESIGNATIONS.split(",")]

    @property
    def activity_types_list(self) -> List[str]:
        return [a.strip() for a in self.ACTIVITY_TYPES.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
