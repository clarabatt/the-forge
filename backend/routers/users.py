from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import User
from backend.database.repositories import LlmUsageLogRepository
from backend.database.session import get_session

router = APIRouter()


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "picture_url": user.picture_url,
        }
    }


@router.get("/me/usage")
def get_usage(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    repo = LlmUsageLogRepository(session)
    llm_usd, infra_usd, taxes_usd, total_usd = repo.get_monthly_cost_totals(user.id, month_start)
    return {
        "cost_usd": round(total_usd, 6),
        "monthly_cap_usd": settings.monthly_cost_cap_usd,
        "breakdown": {
            "llm_usd": round(llm_usd, 6),
            "infra_usd": round(infra_usd, 6),
            "taxes_usd": round(taxes_usd, 6),
        },
    }
