from datetime import datetime
from datetime import timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database.models import User
from backend.database.repositories import LlmUsageLogRepository
from backend.database.session import get_session

router = APIRouter()

# Gemini 1.5 Flash pricing (USD per token)
_INPUT_PRICE_PER_TOKEN = 0.075 / 1_000_000
_OUTPUT_PRICE_PER_TOKEN = 0.30 / 1_000_000


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
    input_tokens, output_tokens = repo.get_monthly_token_totals(user.id, month_start)
    cost_usd = input_tokens * _INPUT_PRICE_PER_TOKEN + output_tokens * _OUTPUT_PRICE_PER_TOKEN
    return {
        "cost_usd": round(cost_usd, 4),
        "monthly_cap_usd": settings.monthly_cost_cap_usd,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
