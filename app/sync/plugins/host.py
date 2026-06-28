"""PluginHost — discovery, DI wiring, guarded dispatch, provider composition."""

import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.db.models import EventLevel
from app.db.repositories import plugins as plugins_repo
from app.sync.plugins.base import PluginBase
from app.sync.plugins.context import PluginContext


@dataclass
class PluginEntry:
    instance: Any
    name: str
    version: str
    enabled: bool = True


class PluginHost:
    """Owns the plugin registry and mediates all engine↔plugin interaction."""

    def __init__(self, ctx_factory=None):
        # ctx_factory(name, config) -> PluginContext. Falls back to a bare ctx.
        self.ctx_factory = ctx_factory
        self.entries: list[PluginEntry] = []

    # ---- registration ---------------------------------------------------
    def register(self, instance, *, name=None, version=None, enabled=True):
        self.entries.append(PluginEntry(
            instance=instance,
            name=name or getattr(instance, "name", instance.__class__.__name__),
            version=version or getattr(instance, "version", "0.0.0"),
            enabled=enabled,
        ))

    def _entry(self, name) -> Optional[PluginEntry]:
        return next((e for e in self.entries if e.name == name), None)

    # ---- dispatch -------------------------------------------------------
    async def dispatch(self, hook, *args, **kwargs):
        """Call an event hook on every enabled plugin; never propagate errors."""
        for e in self.entries:
            if not e.enabled:
                continue
            method = getattr(e.instance, hook, None)
            if method is None:
                continue
            try:
                await method(*args, **kwargs)
            except Exception as ex:  # noqa: BLE001 - guard the engine
                await self._report(e, hook, ex)

    async def collect_naming_tokens(self, item, sub) -> dict:
        """Merge naming tokens contributed by enabled plugins (later wins)."""
        tokens: dict = {}
        for e in self.entries:
            if not e.enabled:
                continue
            fn = getattr(e.instance, "provide_naming_tokens", None)
            if fn is None:
                continue
            try:
                got = await fn(item, sub)
                if got:
                    tokens.update(got)
            except Exception as ex:  # noqa: BLE001
                await self._report(e, "provide_naming_tokens", ex)
        return tokens

    async def collect_path(self, item, sub):
        """First non-None relative path an enabled plugin offers (overrides the
        subscription template). Lets a plugin auto-organize matched media."""
        for e in self.entries:
            if not e.enabled:
                continue
            fn = getattr(e.instance, "provide_path", None)
            if fn is None:
                continue
            try:
                p = await fn(item, sub)
                if p:
                    return p
            except Exception as ex:  # noqa: BLE001
                await self._report(e, "provide_path", ex)
        return None

    async def _report(self, entry, hook, ex):
        msg = f"Plugin {entry.name} error in {hook}: {ex}"
        ctx = getattr(entry.instance, "ctx", None)
        if ctx is None:
            return
        if getattr(ctx, "session_factory", None):
            try:
                await ctx.log(EventLevel.WARNING, "plugin", msg)
                return
            except Exception:  # noqa: BLE001
                pass
        ctx.health["last_error"] = msg

    # ---- discovery (DB-free) -------------------------------------------
    def discover(self, plugins_dir=None):
        """Import plugins/*_plugin.py and register PluginBase subclasses."""
        base = Path(plugins_dir) if plugins_dir else (
            Path(__file__).resolve().parents[3] / "plugins")
        if not base.exists():
            return
        for plugin_file in sorted(base.glob("*_plugin.py")):
            if plugin_file.name == "__init__.py":
                continue
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if not (spec and spec.loader):
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            for obj in vars(module).values():
                if (inspect.isclass(obj) and issubclass(obj, PluginBase)
                        and obj is not PluginBase):
                    cfg = dict(getattr(obj, "default_config", {}) or {})
                    ctx = (self.ctx_factory(obj.name, cfg) if self.ctx_factory
                           else PluginContext(name=obj.name, config=cfg))
                    self.register(obj(ctx), name=obj.name, version=obj.version)

    # ---- DB wiring ------------------------------------------------------
    async def sync_db(self, session_factory):
        """Upsert plugin rows, then load stored enabled flag + config into entries."""
        async with session_factory() as s:
            for e in self.entries:
                row = await plugins_repo.get_by_name(s, e.name)
                if row is None:
                    cfg = (e.instance.ctx.config
                           if getattr(e.instance, "ctx", None) else {})
                    row = await plugins_repo.upsert(
                        s, name=e.name, version=e.version, config=cfg)
                e.enabled = row.enabled
                if row.config and getattr(e.instance, "ctx", None):
                    e.instance.ctx.config = row.config

    # ---- model + router declarations -----------------------------------
    async def create_models(self, engine):
        """create_all the tables declared by every plugin's models()."""
        from app.db.models import Base

        tables = []
        for e in self.entries:
            for model in e.instance.models():
                tables.append(model.__table__)
        if not tables:
            return
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables)
            )

    def all_routers(self) -> list:
        routers = []
        for e in self.entries:
            routers.extend(e.instance.routers())
        return routers

    # ---- management -----------------------------------------------------
    async def set_enabled(self, session_factory, name, enabled: bool):
        """Flip enabled, run the lifecycle hook, and persist the flag."""
        entry = self._entry(name)
        if entry is None:
            return
        entry.enabled = enabled
        hook = "on_enable" if enabled else "on_disable"
        method = getattr(entry.instance, hook, None)
        if method is not None:
            try:
                await method()
            except Exception as ex:  # noqa: BLE001
                await self._report(entry, hook, ex)
        async with session_factory() as s:
            row = await plugins_repo.get_by_name(s, name)
            if row is not None:
                await plugins_repo.set_enabled(s, row.id, enabled)

    def config_schema(self, name) -> Optional[dict]:
        entry = self._entry(name)
        return getattr(entry.instance, "config_schema", None) if entry else None

    def update_config(self, name, config: dict):
        """Push new config into the live plugin's ctx (after a DB save)."""
        entry = self._entry(name)
        if entry and getattr(entry.instance, "ctx", None):
            entry.instance.ctx.config = config

    def health(self, name) -> Optional[dict]:
        entry = self._entry(name)
        if entry is None:
            return None
        ctx = getattr(entry.instance, "ctx", None)
        base = {"loaded_ok": True, "enabled": entry.enabled,
                "last_error": None, "status": {}, "last_run": None}
        if ctx is not None:
            base.update(ctx.health)
            base["enabled"] = entry.enabled  # entry is source of truth
        return base
