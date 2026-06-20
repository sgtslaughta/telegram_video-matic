"""FastAPI dependency injection: DB session and auth."""
import logging
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.engine import get_session
from app.api.auth import verify_session, get_app_password, COOKIE_NAME

logger = logging.getLogger(__name__)

# Track if we've logged the open-mode warning already (per app lifetime)
_open_mode_warned = False


async def get_db(request: Request) -> AsyncSession:
    """Dependency: inject async DB session from app.state."""
    async with request.app.state.async_session() as session:
        yield session


async def require_app_auth(request: Request) -> None:
    """Dependency: verify app password via signed session cookie."""
    global _open_mode_warned

    stored_password = get_app_password()

    if stored_password is None:
        # Open-mode: allow all; warn once per app lifetime
        if not _open_mode_warned:
            logger.warning("TVM_APP_PASSWORD not set; running in open-mode (no auth)")
            _open_mode_warned = True
        return

    token = request.cookies.get(COOKIE_NAME)
    if not token or not verify_session(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
