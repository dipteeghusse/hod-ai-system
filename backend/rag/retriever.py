"""RAG retriever using FAISS + HuggingFace embeddings for department knowledge base."""

import os
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, Docx2txtLoader
)

from config import settings


KNOWLEDGE_BASE_DOCS = """
MITAOE CSE (AI & ML) Department Knowledge Base

ACADEMIC CALENDAR 2025-26:
- Odd Semester: July 2025 - November 2025
- Even Semester: December 2025 - April 2026
- NBA Internal Audit: September 2025
- NAAC Peer Team Visit: February 2026
- End Semester Exams (Odd): November 2025
- End Semester Exams (Even): April 2026
- FDP Week: June 2026

NBA/NAAC COMPLIANCE REQUIREMENTS:
- Course files must be updated every semester with CO-PO mapping, question papers, sample answer books
- Faculty API score should be maintained with evidence of publications, FDP, workshops
- Student CO attainment must be ≥60% of students scoring ≥60%
- Outcome Based Education (OBE) documentation required for all courses
- Criteria 1: Curricular Aspects, Criteria 2: Teaching-Learning, Criteria 3: Research
- Criteria 4: Infrastructure, Criteria 5: Student Support, Criteria 6: Governance
- Criteria 7: Institutional Values

FACULTY ROLES AND RESPONSIBILITIES:
- Course Coordinator: Maintains course file, conducts COs attainment, prepares question papers
- NBA Coordinator: Compiles SAR, organizes internal audits
- Class Coordinator: Monitors attendance, coordinates with students
- Lab Incharge: Manages lab equipment, schedules, maintenance
- Placement Coordinator: Industry connect, internship drives, campus placement
- Research Coordinator: Tracks publications, funded projects, patents
- Activity Coordinator: Organizes events, workshops, competitions

TASK CATEGORIES:
- Academic: Teaching, Assessment, CO-PO mapping, Course files
- Research: Publications, Projects, Patents, Consultancy
- Administrative: Reports, Meetings, Circulars, Approvals
- Student Activities: Attendance, Internships, Placements, Projects
- NBA/NAAC: Compliance, Documentation, Audit preparation
- Events: Workshops, FDPs, Guest Lectures, Industrial Visits
- Examination: Question papers, Invigilation, Result processing

API SCORING (Faculty Performance):
- Scopus/WoS Indexed Journal: 25 points per paper
- UGC CARE List Journal: 15 points per paper
- Conference (Scopus indexed): 20 points per paper
- Conference (others): 5 points per paper
- Patent Granted: 50 points
- Patent Filed: 25 points
- Funded Research Project (PI): 30 points
- FDP/Workshop Organized (>5 days): 10 points
- FDP Attended (>5 days): 5 points
- PhD Awarded under Guidance: 40 points

REMINDER SCHEDULE:
- Critical tasks: 7 days before, 3 days before, 1 day before, day of
- Regular tasks: 3 days before, 1 day before, day of
- Meetings: 1 day before, 1 hour before
- Reports due: 7 days before, 3 days before

DEPARTMENT FACULTY WORKLOAD NORMS:
- Maximum 16 hours teaching load per week per faculty
- Minimum 2 publications per academic year (target)
- Minimum 1 FDP/workshop attendance per semester
- Course coordination for maximum 2 theory + 1 lab per semester
"""


class RAGRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vector_store: Optional[FAISS] = None
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    async def initialize(self):
        store_path = Path(settings.VECTOR_STORE_PATH)
        if store_path.exists():
            self.vector_store = FAISS.load_local(
                str(store_path), self.embeddings, allow_dangerous_deserialization=True
            )
        else:
            await self._build_initial_store()

    async def _build_initial_store(self):
        docs = [Document(page_content=KNOWLEDGE_BASE_DOCS, metadata={"source": "department_kb"})]
        docs_dir = Path("./rag/sample_docs")
        if docs_dir.exists():
            for f in docs_dir.iterdir():
                try:
                    if f.suffix == ".pdf":
                        loader = PyPDFLoader(str(f))
                    elif f.suffix in (".docx", ".doc"):
                        loader = Docx2txtLoader(str(f))
                    elif f.suffix == ".txt":
                        loader = TextLoader(str(f))
                    else:
                        continue
                    docs.extend(loader.load())
                except Exception:
                    pass

        chunks = self.splitter.split_documents(docs)
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(settings.VECTOR_STORE_PATH)

    def retrieve(self, query: str, k: int = 4) -> str:
        if not self.vector_store:
            return ""
        docs = self.vector_store.similarity_search(query, k=k)
        return "\n\n".join(d.page_content for d in docs)

    def add_document(self, content: str, metadata: dict = {}):
        chunks = self.splitter.split_documents(
            [Document(page_content=content, metadata=metadata)]
        )
        if self.vector_store:
            self.vector_store.add_documents(chunks)
            self.vector_store.save_local(settings.VECTOR_STORE_PATH)


rag_retriever = RAGRetriever()
