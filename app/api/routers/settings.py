"""Settings router — get/patch runtime settings."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import SettingRead, SettingPatchRequest
from app.db.repositories import settings

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(require_app_auth)],
)


# Owned by dedicated routers (hold encrypted secrets); hide from the generic list.
_PRIVATE = {"notify_targets", "notify_options", "jellyfin", "last_visit_at"}


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """GET /api/settings — list all settings."""
    items = await settings.list(db)
    return [SettingRead.from_orm(s) for s in items if s.key not in _PRIVATE]


@router.patch("")
async def patch_settings(
    req: SettingPatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """PATCH /api/settings — update settings."""
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        await settings.set(db, key, str(value))

    items = await settings.list(db)
    return [SettingRead.from_orm(s) for s in items if s.key not in _PRIVATE]
