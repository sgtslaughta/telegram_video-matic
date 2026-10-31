"""Discovery matching only runs for items that will actually download."""
from types import SimpleNamespace

import pytest

from app.db.models import MediaStatus
from plugins.rugby_plugin import RugbyPlugin


@pytest.mark.asyncio
@pytest.mark.parametrize("status,calls", [(MediaStatus.PENDING, 1), (MediaStatus.SKIPPED, 0)])
async def test_discovery_skips_filtered_items(status, calls):
    seen = []

    async def match_item(item):
        seen.append(item)

    p = RugbyPlugin(ctx=None)
    p.service = SimpleNamespace(match_item=match_item)
    await p.on_media_discovered(SimpleNamespace(status=status))
    assert len(seen) == calls
