"""Rugby enrichment plugin — organises rugby videos by league/season/teams.

Thin entry point: all logic lives in app.rugby. Rides the Layer-1 platform
(context injection, provider hook, plugin-owned models + router).
"""

from pathlib import Path

from app.sync.plugins import PluginBase
from app.rugby import models as rm
from app.rugby.router import router as rugby_router
from app.rugby.service import RugbyService


class RugbyPlugin(PluginBase):
    name = "rugby"
    version = "1.0.0"
    default_config = {"api_key": "123", "min_interval": 2.0, "jellyfin_artwork": True}
    config_schema = {
        "fields": [
            {"key": "api_key", "type": "string", "label": "TheSportsDB API key",
             "help": "Free tier is '123'. Paid key raises rate limits."},
            {"key": "min_interval", "type": "number", "label": "Min seconds between API calls"},
            {"key": "jellyfin_artwork", "type": "boolean",
             "label": "Write team badge as poster.jpg for Jellyfin"},
        ]
    }

    def __init__(self, ctx=None):
        super().__init__(ctx)
        self.service = RugbyService(ctx) if ctx else None

    # --- platform declarations ---
    def models(self):
        return rm.ALL_MODELS

    def routers(self):
        return [rugby_router]

    # --- lifecycle ---
    async def on_enable(self):
        if self.service is None:
            return
        # Seed the league catalog if we have none yet (cheap, idempotent).
        leagues = await self.service.list_leagues()
        if not leagues:
            await self.service.refresh_catalog()

    # --- event hooks ---
    async def on_media_discovered(self, item):
        if self.service:
            await self.service.match_item(item)

    async def on_post_download(self, item, path):
        """Write a rich Jellyfin NFO (teams as actors) + poster beside the file."""
        if not self.service or not self.ctx.config.get("jellyfin_artwork"):
            return
        await self.service.write_jellyfin(item, Path(path))

    # --- provider hook (host merges into naming tokens) ---
    async def provide_naming_tokens(self, item, sub):
        if not self.service:
            return {}
        return await self.service.naming_tokens(item.id)
