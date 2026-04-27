"""
Seed the dev database with a test user and sample applications.

Usage:
    uv run python -m backend.scripts.seed

After running, paste the printed cookie command into the browser console
while the frontend is open at http://localhost:5173.
"""

from sqlmodel import Session, select

from backend.database.models import (
    Application,
    ApplicationStatus,
    PipelineStatus,
    Resume,
    ResumeType,
    User,
)
from backend.database.session import engine


def seed() -> None:
    with Session(engine) as session:
        # ── User ──────────────────────────────────────────────────────────────
        user = session.exec(
            select(User).where(User.email == "dev@theforge.local")
        ).first()
        if not user:
            user = User(
                email="dev@theforge.local",
                google_sub="dev-seed-google-sub-001",
                full_name="Dev User",
                is_active=True,
            )
            session.add(user)
            session.flush()
            print(f"  created user  {user.id}")
        else:
            print(f"  found user    {user.id}")

        # ── Base resume ───────────────────────────────────────────────────────
        existing_resumes = session.exec(
            select(Resume).where(Resume.user_id == user.id)
        ).all()
        if not existing_resumes:
            resume = Resume(
                user_id=user.id,
                file_name="dev_resume_v1.docx",
                bucket_key=f"resumes/{user.id}/base_v1.docx",
                resume_type=ResumeType.BASE,
                is_latest=True,
                version_number=1,
                raw_text=(
                    "Dev User\n"
                    "dev@theforge.local · github.com/devuser\n\n"
                    "EXPERIENCE\n"
                    "Senior Software Engineer — Acme Corp (2021–present)\n"
                    "  · Built distributed systems handling 50k req/s\n"
                    "  · Led migration from monolith to microservices\n\n"
                    "Software Engineer — Startup Inc. (2018–2021)\n"
                    "  · Full-stack development with Python and Vue.js\n\n"
                    "EDUCATION\n"
                    "BSc Computer Science — State University (2018)\n\n"
                    "SKILLS\n"
                    "Python, TypeScript, PostgreSQL, Docker, Kubernetes, FastAPI"
                ),
            )
            session.add(resume)
            session.flush()
            print(f"  created resume {resume.id}")

        # ── Applications ──────────────────────────────────────────────────────
        existing_apps = session.exec(
            select(Application).where(Application.user_id == user.id)
        ).all()
        if not existing_apps:
            apps = [
                Application(
                    user_id=user.id,
                    company_name="Stripe",
                    job_title="Senior Software Engineer",
                    job_description="Build the economic infrastructure of the internet.",
                    status=PipelineStatus.READY,
                    application_status=ApplicationStatus.applied,
                ),
                Application(
                    user_id=user.id,
                    company_name="Linear",
                    job_title="Staff Engineer",
                    job_description="Shape the future of project management tooling.",
                    status=PipelineStatus.PENDING_APPROVAL,
                    application_status=ApplicationStatus.applied,
                ),
                Application(
                    user_id=user.id,
                    company_name="Vercel",
                    job_title="Frontend Infrastructure Engineer",
                    job_description="Make the web faster for everyone.",
                    status=PipelineStatus.ANALYZING,
                    application_status=ApplicationStatus.applied,
                ),
                Application(
                    user_id=user.id,
                    company_name="Anthropic",
                    job_title="Research Engineer",
                    job_description="Work on frontier AI safety research.",
                    status=PipelineStatus.UPLOADED,
                    application_status=ApplicationStatus.applied,
                ),
                Application(
                    user_id=user.id,
                    company_name="Figma",
                    job_title="Design Systems Engineer",
                    job_description="Build the tools that designers use every day.",
                    status=PipelineStatus.FAILED,
                    application_status=ApplicationStatus.denied,
                ),
            ]
            for app in apps:
                session.add(app)
            print(f"  created {len(apps)} applications")

        session.commit()

    print("\n✓ Seed complete\n")
    print("Log in as the dev user by visiting:\n")
    print("http://localhost:8000/docs, find POST /api/dev/login, click Try it out → Execute.\n") 
    print("Or with curl:\n")
    print("  curl -X POST http://localhost:8000/api/dev/login\n")


if __name__ == "__main__":
    seed()
