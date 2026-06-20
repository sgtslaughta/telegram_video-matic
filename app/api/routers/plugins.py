"""Plugins router — list and patch plugin config."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import PluginRead, PluginPatchRequest
from app.db.repositories import plugins

router = APIRouter(
    prefix="/api/plugins",
    tags=["plugins"],
    dependencies=[Depends(require_app_auth)],
)


@router.get("")
async def list_plugins(db: AsyncSession = Depends(get_db)):
    """GET /api/plugins — list installed plugins."""
    items = await plugins.list(db)
    return [PluginRead.from_orm(p) for p in items]


@router.patch("/{plugin_name}")
async def patch_plugin(
    plugin_name: str,
    req: PluginPatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """PATCH /api/plugins/{name} — enable/update plugin config."""
    plugin = await plugins.get_by_name(db, plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    update_data = req.model_dump(exclude_unset=True)
    updated = await plugins.update(db, plugin.id, **update_data)
    return PluginRead.from_orm(updated)
