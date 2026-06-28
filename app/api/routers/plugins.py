"""Plugins router — list (with health) and patch (config + host lifecycle)."""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import PluginRead, PluginPatchRequest
from app.db.repositories import plugins

router = APIRouter(
    prefix="/api/plugins",
    tags=["plugins"],
    dependencies=[Depends(require_app_auth)],
)


def _merge_health(data: dict, host, name: str) -> dict:
    """Overlay live host health (enabled, last_error, status, schema) onto a row."""
    if host is None:
        return data
    health = host.health(name)
    if health:
        data["enabled"] = health["enabled"]
        data["last_error"] = health.get("last_error")
        data["status"] = health.get("status")
        data["loaded_ok"] = health.get("loaded_ok", True)
    data["config_schema"] = host.config_schema(name)
    return data


@router.get("")
async def list_plugins(request: Request, db: AsyncSession = Depends(get_db)):
    """GET /api/plugins — installed plugins with live health/config schema."""
    host = getattr(request.app.state, "plugin_host", None)
    items = await plugins.list(db)
    return [_merge_health(PluginRead.from_orm(p).model_dump(), host, p.name)
            for p in items]


@router.patch("/{plugin_name}")
async def patch_plugin(
    plugin_name: str,
    req: PluginPatchRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """PATCH /api/plugins/{name} — update config and/or enable/disable.

    Enable/disable goes through the host so lifecycle hooks fire and dispatch
    gating updates; falls back to a plain DB write if no host is wired.
    """
    plugin = await plugins.get_by_name(db, plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    host = getattr(request.app.state, "plugin_host", None)
    factory = (getattr(request.app.state, "session_factory", None)
               or getattr(request.app.state, "async_session", None))
    data = req.model_dump(exclude_unset=True)

    if "config" in data:
        await plugins.update(db, plugin.id, config=data["config"])
        if host:
            host.update_config(plugin_name, data["config"])

    if "enabled" in data:
        if host and factory:
            await host.set_enabled(factory, plugin_name, data["enabled"])
        else:
            await plugins.set_enabled(db, plugin.id, data["enabled"])

    updated = await plugins.get_by_name(db, plugin_name)
    return _merge_health(PluginRead.from_orm(updated).model_dump(), host, plugin_name)
