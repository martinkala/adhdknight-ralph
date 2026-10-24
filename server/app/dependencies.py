from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_monitoring_operator(x_monitoring_key: str = Header(default="")) -> None:
    """Restricts `/internal/monitoring/*` to operators (contracts/monitoring-status.md):
    a shared key, not a full RBAC system, matches this single-server personal deployment's
    scale — same reasoning research.md gives for rejecting heavier monitoring/secrets infra."""
    settings = get_settings()
    if not settings.monitoring_api_key or x_monitoring_key != settings.monitoring_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing monitoring key")


def get_now() -> datetime:
    """Current UTC time; tests override this dependency to fake the clock."""
    return datetime.now(timezone.utc)
