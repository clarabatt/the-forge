import uuid
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from backend.database.models import (
    AgentName,
    Application,
    ApplicationStatus,
    ChatMessage,
    ChatRole,
    CoverLetter,
    LlmUsageLog,
    OAuthState,
    PipelineStatus,
    Resume,
    ResumeType,
    Skill,
    SkillMatchStatus,
    User,
)


@pytest.fixture
def UserFactory(session: Session):
    def factory(**kwargs) -> User:
        user = User(
            email=kwargs.get("email", f"user-{uuid.uuid4()}@example.com"),
            google_sub=kwargs.get("google_sub", str(uuid.uuid4())),
            full_name=kwargs.get("full_name", "Test User"),
            picture_url=kwargs.get("picture_url", None),
            is_active=kwargs.get("is_active", True),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return factory


@pytest.fixture
def ApplicationFactory(session: Session, UserFactory):
    def factory(**kwargs) -> Application:
        if "user_id" not in kwargs:
            kwargs["user_id"] = UserFactory().id
        app = Application(
            user_id=kwargs["user_id"],
            company_name=kwargs.get("company_name", "Acme Corp"),
            job_title=kwargs.get("job_title", "Software Engineer"),
            job_description=kwargs.get("job_description", "Build cool stuff."),
            status=kwargs.get("status", PipelineStatus.UPLOADED),
            application_status=kwargs.get("application_status", ApplicationStatus.applied),
            base_resume_id=kwargs.get("base_resume_id", None),
            retry_count=kwargs.get("retry_count", 0),
            analysis_feedback=kwargs.get("analysis_feedback", None),
        )
        session.add(app)
        session.commit()
        session.refresh(app)
        return app

    return factory


@pytest.fixture
def ResumeFactory(session: Session, UserFactory):
    def factory(**kwargs) -> Resume:
        if "user_id" not in kwargs:
            kwargs["user_id"] = UserFactory().id
        resume = Resume(
            user_id=kwargs["user_id"],
            application_id=kwargs.get("application_id", None),
            file_name=kwargs.get("file_name", "resume.docx"),
            bucket_key=kwargs.get("bucket_key", f"resumes/{uuid.uuid4()}.docx"),
            resume_type=kwargs.get("resume_type", ResumeType.BASE),
            is_latest=kwargs.get("is_latest", True),
            version_number=kwargs.get("version_number", 1),
            raw_text=kwargs.get("raw_text", None),
            parent_resume_id=kwargs.get("parent_resume_id", None),
        )
        session.add(resume)
        session.commit()
        session.refresh(resume)
        return resume

    return factory


@pytest.fixture
def SkillFactory(session: Session, ApplicationFactory):
    def factory(**kwargs) -> Skill:
        if "application_id" not in kwargs:
            kwargs["application_id"] = ApplicationFactory().id
        skill = Skill(
            application_id=kwargs["application_id"],
            skill_name=kwargs.get("skill_name", "Python"),
            category=kwargs.get("category", "Programming"),
            match_status=kwargs.get("match_status", SkillMatchStatus.found_in_resume),
            ai_confidence=kwargs.get("ai_confidence", 0.9),
            rank=kwargs.get("rank", 1),
            user_action=kwargs.get("user_action", None),
            required=kwargs.get("required", True),
        )
        session.add(skill)
        session.commit()
        session.refresh(skill)
        return skill

    return factory


@pytest.fixture
def LlmUsageLogFactory(session: Session, UserFactory):
    def factory(**kwargs) -> LlmUsageLog:
        if "user_id" not in kwargs:
            kwargs["user_id"] = UserFactory().id
        log = LlmUsageLog(
            user_id=kwargs["user_id"],
            application_id=kwargs.get("application_id", None),
            agent_name=kwargs.get("agent_name", AgentName.JD),
            model=kwargs.get("model", "claude-haiku-4-5"),
            input_tokens=kwargs.get("input_tokens", 100),
            output_tokens=kwargs.get("output_tokens", 50),
            created_at=kwargs.get("created_at", datetime.utcnow()),
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log

    return factory


@pytest.fixture
def OAuthStateFactory(session: Session):
    def factory(**kwargs) -> OAuthState:
        state = OAuthState(
            state=kwargs.get("state", str(uuid.uuid4())),
            expires_at=kwargs.get(
                "expires_at", datetime.utcnow() + timedelta(minutes=10)
            ),
        )
        session.add(state)
        session.commit()
        session.refresh(state)
        return state

    return factory


@pytest.fixture
def CoverLetterFactory(session: Session, ApplicationFactory):
    def factory(**kwargs) -> CoverLetter:
        if "application_id" not in kwargs:
            kwargs["application_id"] = ApplicationFactory().id
        cl = CoverLetter(
            application_id=kwargs["application_id"],
            content=kwargs.get("content", "Dear Hiring Manager, I am writing to express my interest…"),
            questions=kwargs.get("questions", None),
        )
        session.add(cl)
        session.commit()
        session.refresh(cl)
        return cl

    return factory


@pytest.fixture
def ChatMessageFactory(session: Session, ApplicationFactory):
    def factory(**kwargs) -> ChatMessage:
        if "application_id" not in kwargs:
            kwargs["application_id"] = ApplicationFactory().id
        msg = ChatMessage(
            application_id=kwargs["application_id"],
            role=kwargs.get("role", ChatRole.user),
            content=kwargs.get("content", "Hello!"),
        )
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg

    return factory
