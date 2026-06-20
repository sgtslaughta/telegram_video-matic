"""Telegram login state machine router."""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import (
    TelegramStatusRead,
    TelegramPhoneRequest,
    TelegramCodeRequest,
    TelegramPasswordRequest,
)

# Build router with optional auth dependency (controlled by require_app_auth)
router = APIRouter(prefix="/api/tg", tags=["telegram"])


async def _get_tg_status(request: Request) -> TelegramStatusRead:
    """Helper to get current Telegram account status."""
    svc = request.app.state.tg_service
    account = svc.account
    if not account:
        raise HTTPException(status_code=500, detail="Account not initialized")
    return TelegramStatusRead(
        status=account.status.value,
        username=account.username,
        display_name=account.display_name,
        phone=account.phone,
    )


@router.get("/status", dependencies=[Depends(require_app_auth)])
async def tg_status(request: Request):
    """GET /api/tg/status — current Telegram account state."""
    return await _get_tg_status(request)


@router.post("/login", dependencies=[Depends(require_app_auth)])
async def tg_login(req: TelegramPhoneRequest, request: Request):
    """POST /api/tg/login — initiate login with phone."""
    svc = request.app.state.tg_service
    try:
        await svc.start_login(req.phone)
        return await _get_tg_status(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/code", dependencies=[Depends(require_app_auth)])
async def tg_code(req: TelegramCodeRequest, request: Request):
    """POST /api/tg/code — submit login code."""
    svc = request.app.state.tg_service
    try:
        await svc.submit_code(req.code)
        return await _get_tg_status(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password", dependencies=[Depends(require_app_auth)])
async def tg_password(req: TelegramPasswordRequest, request: Request):
    """POST /api/tg/password — submit 2FA password."""
    svc = request.app.state.tg_service
    try:
        await svc.submit_password(req.password)
        return await _get_tg_status(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout", dependencies=[Depends(require_app_auth)])
async def tg_logout(request: Request):
    """POST /api/tg/logout — disconnect Telegram session."""
    svc = request.app.state.tg_service
    try:
        await svc.logout()
        return await _get_tg_status(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
