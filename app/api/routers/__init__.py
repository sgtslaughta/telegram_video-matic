"""API routers package. Re-export router modules for registration in main.py."""
from . import (
    health,
    auth,
    telegram,
    channels,
    subscriptions,
    media,
    downloads,
    events,
    settings,
    plugins,
    fs,
    notifications,
)

__all__ = [
    "health",
    "auth",
    "telegram",
    "channels",
    "subscriptions",
    "media",
    "downloads",
    "events",
    "settings",
    "plugins",
    "fs",
    "notifications",
]
