"""Telegram login state machine router."""
from fastapi import APIRouter, HTTPException, Depends, Request
from app.api.deps import require_app_auth
from app.api.schemas import (
    TelegramStatusRead,
    TelegramCredentialsRequest,
    TelegramPhoneRequest,
    TelegramCodeRequest,
    TelegramPasswordRequest,
)

# Build router with optional auth dependency (controlled by require_app_auth)
router = APIRouter(prefix="/api/tg", tags=["telegram"])


async def _get_tg_status(request: Request) -> TelegramStatusRead:
    """Helper to get current Telegram account status."""
    svc = request.app.state.tg_service
    # Read fresh from DB: login mutations update the row, not the cached
    # svc.account, so the in-memory copy can be stale (e.g. still 'awaiting_code'
    # after a successful sign-in). Keep svc.account in sync for service use.
    account = await svc.account_repo.get()
    svc.account = account
    if not account:
        # Fresh install / not yet configured: report disconnected so the UI
        # shows the credentials step rather than erroring.
        return TelegramStatusRead(
            status="disconnected", configured=False,
            username=None, display_name=None, phone=None
        )
    return TelegramStatusRead(
        status=str(account.status),
        configured=bool(account.api_id_enc),
        username=account.username,
        display_name=account.display_name,
        phone=account.phone,
    )


@router.get("/status", dependencies=[Depends(require_app_auth)])
async def tg_status(request: Request):
    """GET /api/tg/status — current Telegram account state."""
    return await _get_tg_status(request)


@router.post("/credentials", dependencies=[Depends(require_app_auth)])
async def tg_credentials(req: TelegramCredentialsRequest, request: Request):
    """POST /api/tg/credentials — store API id/hash and build the client."""
    svc = request.app.state.tg_service
    try:
        await svc.set_credentials(req.api_id, req.api_hash)
        return await _get_tg_status(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
