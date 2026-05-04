import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class PipelineStatus(str, Enum):
    UPLOADED = "UPLOADED"
    ANALYZING = "ANALYZING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    TAILORING = "TAILORING"
    VALIDATING = "VALIDATING"
    PENDING_RETRY = "PENDING_RETRY"
    READY = "READY"
    FAILED = "FAILED"


class ApplicationStatus(str, Enum):
    applied = "applied"
    denied = "denied"
    cancelled = "cancelled"
    approved = "approved"


class ResumeType(str, Enum):
    BASE = "BASE"
    TAILORED = "TAILORED"


class SkillMatchStatus(str, Enum):
    found_in_resume = "found_in_resume"
    missing = "missing"


class SkillUserAction(str, Enum):
    include = "include"
    exclude = "exclude"
    rephrase = "rephrase"


class AgentName(str, Enum):
    JD = "JD"
    RESUME = "RESUME"
    DIFF = "DIFF"
    JUDGE_RETRY = "JUDGE_RETRY"
    COVER_LETTER = "COVER_LETTER"
    SKILL_VERIFIER = "SKILL_VERIFIER"


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    google_sub: str = Field(unique=True, index=True)
    full_name: str
    picture_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)

    applications: list["Application"] = Relationship(back_populates="user")
    resumes: list["Resume"] = Relationship(back_populates="user")
    llm_usage_logs: list["LlmUsageLog"] = Relationship(back_populates="user")


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    status: PipelineStatus = Field(default=PipelineStatus.UPLOADED)
    company_name: str
    job_title: str
    job_description: str
    application_status: ApplicationStatus = Field(default=ApplicationStatus.applied)
    base_resume_id: Optional[uuid.UUID] = Field(default=None, foreign_key="resumes.id")
    template_version: str = Field(default="v1")
    retry_count: int = Field(default=0)
    error_message: Optional[str] = None
    analysis_feedback: Optional[str] = None  # JSON string: {overall_assessment, strong_points, weak_points, recommended_changes}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="applications")
    skills: list["Skill"] = Relationship(back_populates="application")
    llm_usage_logs: list["LlmUsageLog"] = Relationship(back_populates="application")
    chat_messages: list["ChatMessage"] = Relationship(back_populates="application")
    cover_letter: Optional["CoverLetter"] = Relationship(back_populates="application")


class Resume(SQLModel, table=True):
    __tablename__ = "resumes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    application_id: Optional[uuid.UUID] = Field(default=None, foreign_key="applications.id")
    file_name: str
    bucket_key: str
    raw_text: Optional[str] = None
    resume_type: ResumeType = Field(default=ResumeType.BASE)
    parent_resume_id: Optional[uuid.UUID] = Field(default=None, foreign_key="resumes.id")
    version_number: int = Field(default=1)
    is_latest: bool = Field(default=True, index=True)
    template_version: str = Field(default="v1")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="resumes")


class Skill(SQLModel, table=True):
    __tablename__ = "skills"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    skill_name: str
    category: str
    match_status: SkillMatchStatus
    user_action: Optional[SkillUserAction] = None
    ai_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rank: int
    required: bool = Field(default=True)

    application: Optional[Application] = Relationship(back_populates="skills")


class LlmUsageLog(SQLModel, table=True):
    __tablename__ = "llm_usage_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    application_id: Optional[uuid.UUID] = Field(default=None, foreign_key="applications.id")
    agent_name: AgentName
    model: str
    input_tokens: int
    output_tokens: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="llm_usage_logs")
    application: Optional[Application] = Relationship(back_populates="llm_usage_logs")


class OAuthState(SQLModel, table=True):
    __tablename__ = "oauth_states"

    state: str = Field(primary_key=True)
    expires_at: datetime


class CoverLetter(SQLModel, table=True):
    __tablename__ = "cover_letters"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id", index=True)
    content: str
    questions: Optional[str] = None  # JSON array of strings
    created_at: datetime = Field(default_factory=datetime.utcnow)

    application: Optional["Application"] = Relationship(back_populates="cover_letter")


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    application_id: uuid.UUID = Field(foreign_key="applications.id")
    role: ChatRole
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    application: Optional[Application] = Relationship(back_populates="chat_messages")
