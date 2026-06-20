"""API routers package."""
from . import (
    auth,
    telegram,
    channels,
    subscriptions,
    media,
    downloads,
    events,
    settings,
    plugins,
)

# Import health router for registration in main.py
from . import health  # noqa: F401
