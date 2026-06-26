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

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # App
    APP_NAME: str = "HOD AI System - MITAOE CSE-AIML"
    HOD_EMAIL: str = "hodaiml_AI@mitaoe.ac.in"
    DEPARTMENT: str = "CSE (AI & ML)"
    INSTITUTION: str = "MITAOE"
    ACADEMIC_YEAR: str = "2025-26"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # RAG
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_PATH: str = "./rag/vector_store"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Configure LangSmith environment
os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGCHAIN_TRACING_V2).lower()
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
