"""Authentication router."""
from fastapi import APIRouter, HTTPException, Response, Request
from app.api.schemas import LoginRequest, AuthMeRead
from app.api.auth import (
    sign_session,
    check_app_password,
    get_app_password,
    verify_session,
    COOKIE_NAME,
    COOKIE_MAX_AGE,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(req: LoginRequest, response: Response):
    """POST /api/auth/login — check app password, set session cookie."""
    if not check_app_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = sign_session(req.password)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="strict",
    )
    return {"authenticated": True}


@router.post("/logout")
async def logout(response: Response):
    """POST /api/auth/logout — clear session cookie."""
    response.delete_cookie(COOKIE_NAME)
    return {"authenticated": False}


@router.get("/me")
async def me(request: Request):
    """GET /api/auth/me — check auth status."""
    token = request.cookies.get(COOKIE_NAME)
    authenticated = bool(token and verify_session(token))
    password_set = get_app_password() is not None
    return AuthMeRead(authenticated=authenticated, password_set=password_set)
