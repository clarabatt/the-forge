import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from backend.config import settings
from backend.database.models import OAuthState
from backend.database.session import get_session

router = APIRouter()


@router.get("/google/login")
async def google_login(session: Session = Depends(get_session)):
    state = secrets.token_urlsafe(32)
    from datetime import datetime, timedelta
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    session.add(OAuthState(state=state, expires_at=expires_at))
    session.commit()

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    from datetime import datetime
    row = session.exec(
        select(OAuthState).where(
            OAuthState.state == state,
            OAuthState.expires_at > datetime.utcnow(),
        )
    ).first()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    session.delete(row)
    session.commit()

    # TODO: exchange code for tokens, upsert User, issue session token
    return {"status": "ok", "code": code}
