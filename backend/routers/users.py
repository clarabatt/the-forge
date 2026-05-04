from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import User
from backend.database.repositories import LlmUsageLogRepository
from backend.database.session import get_session
from backend.pricing import token_cost

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
    breakdown = repo.get_monthly_tokens_by_model(user.id, month_start)
    cost_usd = sum(token_cost(model, inp, out) for model, inp, out in breakdown)
    input_tokens = sum(inp for _, inp, _ in breakdown)
    output_tokens = sum(out for _, _, out in breakdown)
    return {
        "cost_usd": round(cost_usd, 6),
        "monthly_cap_usd": settings.monthly_cost_cap_usd,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
