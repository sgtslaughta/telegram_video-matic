"""PluginContext — what the host injects into every plugin.

Replaces the old global-reaching backdoor: a plugin gets its DB session,
its stored config, app settings, and a logger that writes Events + tracks health.
"""

from contextlib import asynccontextmanager

from app.db.models import EventLevel
from app.db.repositories import events

_ERROR_LEVELS = {str(EventLevel.WARNING), str(EventLevel.ERROR)}


class PluginContext:
    def __init__(self, name, config=None, settings=None,
                 media_root="/downloads", session_factory=None):
        self.name = name
        self.config = config if config is not None else {}
        self.settings = settings
        self.media_root = media_root
        self.session_factory = session_factory
        self.health = {"last_error": None, "status": {}, "last_run": None}

    @asynccontextmanager
    async def session(self):
        if self.session_factory is None:
            raise RuntimeError(f"PluginContext({self.name}) has no session_factory")
        async with self.session_factory() as s:
            yield s

    async def log(self, level, kind, message, *, subscription_id=None, media_id=None):
        """Write an Event and, for warnings/errors, record last_error for the UI."""
        if str(level) in _ERROR_LEVELS:
            self.health["last_error"] = message
        if self.session_factory is not None:
            async with self.session() as s:
                await events.add(s, level=str(level), kind=kind, message=message,
                                 subscription_id=subscription_id, media_id=media_id)

    def set_status(self, status: dict):
        """Publish a health snapshot (e.g. {'leagues': 6, 'last_scrape': ...})."""
        self.health["status"] = status

    def clear_error(self):
        self.health["last_error"] = None
