"""
RAG Retriever — FAISS + HuggingFace embeddings.
The knowledge base is seeded from config values and any documents in rag/sample_docs/.
No hardcoded institution/subject names.
"""

from pathlib import Path
from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader

from config import settings


def _build_knowledge_base() -> str:
    """Build the base knowledge document dynamically from config — no hardcoded values."""
    criteria_lines = "\n".join(
        f"  - Criterion {k}: {v}"
        for k, v in settings.accreditation_criteria_dict.items()
    )
    return f"""
Department Knowledge Base
=========================
Institution  : {settings.INSTITUTION}
Department   : {settings.DEPARTMENT}
Program      : {settings.PROGRAM_LEVEL}
Academic Year: {settings.ACADEMIC_YEAR}
Accreditation: {settings.ACCREDITATION_BODY}

TASK CATEGORIES:
{chr(10).join("  - " + c for c in settings.task_categories_list)}

SUBJECTS / COURSES:
{chr(10).join("  - " + s for s in settings.subjects_list)}

FACULTY DESIGNATIONS:
{chr(10).join("  - " + d for d in settings.designations_list)}

ACTIVITY TYPES (for performance scoring):
{chr(10).join("  - " + a for a in settings.activity_types_list)}

{settings.ACCREDITATION_BODY} CRITERIA:
{criteria_lines}

GENERAL ACADEMIC NORMS:
- Course files must be updated every semester with CO-PO mapping,
  question papers, and sample answer books.
- CO attainment target: ≥60% of students scoring ≥60% per CO.
- Outcome-Based Education (OBE) documentation required for all courses.
- Faculty API scoring follows UGC/AICTE norms unless institution specifies otherwise.

REMINDER SCHEDULE:
- Critical tasks  : 7 days before, 3 days before, 1 day before, day of
- Regular tasks   : 3 days before, 1 day before, day of
- Meetings        : 1 day before, 1 hour before
- Reports due     : 7 days before, 3 days before

FACULTY WORKLOAD NORMS:
- Maximum ~16 lecture hours per week per faculty.
- Course coordination: maximum 2 theory + 1 lab per semester.
- Minimum 1 FDP/workshop attendance per semester.
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
            await self._build()

    async def _build(self):
        docs = [Document(
            page_content=_build_knowledge_base(),
            metadata={"source": "department_config_kb"},
        )]

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
        """Add any new document (circular, policy, guideline) to the knowledge base."""
        chunks = self.splitter.split_documents(
            [Document(page_content=content, metadata=metadata)]
        )
        if self.vector_store:
            self.vector_store.add_documents(chunks)
            self.vector_store.save_local(settings.VECTOR_STORE_PATH)

    def rebuild(self):
        """Rebuild the vector store — call after changing config subjects/categories."""
        import asyncio
        if Path(settings.VECTOR_STORE_PATH).exists():
            import shutil
            shutil.rmtree(settings.VECTOR_STORE_PATH)
        asyncio.run(self._build())


rag_retriever = RAGRetriever()
