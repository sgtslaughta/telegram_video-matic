"""Plugin protocol + base class with no-op defaults.

Plugins subclass ``PluginBase`` and override only the capabilities they need.
The host injects a ``PluginContext`` (DB session, config, logger) at construction.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TVMPlugin(Protocol):
    """Structural type for the core event hooks (kept for typing)."""

    async def on_media_discovered(self, item) -> None: ...
    async def on_pre_download(self, item) -> None: ...
    async def on_post_download(self, item, path: str) -> None: ...
    async def on_prune(self, item) -> None: ...


class PluginBase:
    """Concrete base: override what you need, inherit no-ops for the rest."""

    # --- manifest (override on subclass) ---
    name: str = "unnamed"
    version: str = "0.0.0"
    default_config: dict = {}
    config_schema: dict | None = None

    def __init__(self, ctx=None):
        self.ctx = ctx

    # --- event hooks (notify; return None) ---
    async def on_media_discovered(self, item) -> None: ...
    async def on_pre_download(self, item) -> None: ...
    async def on_post_download(self, item, path: str) -> None: ...
    async def on_prune(self, item) -> None: ...

    # --- lifecycle ---
    async def on_enable(self) -> None: ...
    async def on_disable(self) -> None: ...

    # --- provider hook (host composes the returned dict) ---
    async def provide_naming_tokens(self, item, sub) -> dict:
        return {}

    # --- declarations (host consumes) ---
    def models(self) -> list:
        """SQLAlchemy model classes (on the shared Base) the host create_all's."""
        return []

    def routers(self) -> list:
        """FastAPI APIRouters the host mounts under /api/plugins/{name}."""
        return []

    def background_tasks(self) -> list:
        """Coroutine factories the host supervises while the plugin is enabled."""
        return []
