"""Rugby wanted: fixtures played but not downloaded, with auto-search capability."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import and_, select

from app.db.models import MediaItem, MediaStatus, Subscription
from app.rugby.models import (
    RugbyFixture, RugbyLeague, RugbyMatch, RugbySubscription, RugbyWantedState,
)


class WantedService:
    """Manage rugby wanted list: query, search, grab, dismiss, auto-search."""

    def __init__(self, ctx):
        self.ctx = ctx

    async def list_wanted(self, lookback_days: int = 60) -> list[dict]:
        """Fixtures played but not downloaded, within lookback window, not dismissed.

        Returns items shaped: {fixture_id, league, season, round, home, away, date,
        days_missing, last_searched_at, attempts, state, subscription_id}
        """
        now = datetime.now(timezone.utc)
        playback_cutoff = now - timedelta(hours=3)
        lookback_date = now - timedelta(days=lookback_days)

        async with self.ctx.session() as s:
            # Get all subscribed leagues and their subscription dates
            subs = (
                await s.execute(
                    select(RugbySubscription, Subscription).where(
                        RugbySubscription.subscription_id == Subscription.id
                    )
                )
            ).all()

            wanted = []
            for rugby_sub, core_sub in subs:
                league_id = rugby_sub.league_id
                # Determine subscription start date
                sub_date_from = core_sub.date_from or (now - timedelta(days=lookback_days))
                # Ensure timezone-aware
                sub_date_from = (
                    sub_date_from
                    if sub_date_from.tzinfo
                    else sub_date_from.replace(tzinfo=timezone.utc)
                )
                # Window start is the later of subscription start or default lookback
                window_start = max(sub_date_from, lookback_date)

                # Get all fixtures in this league within window that are played
                fixtures = (
                    await s.execute(
                        select(RugbyFixture).where(
                            and_(
                                RugbyFixture.league_id == league_id,
                                RugbyFixture.date >= window_start,
                                RugbyFixture.date < playback_cutoff,
                            )
                        )
                    )
                ).scalars().all()

                # For each fixture, check if it's already matched and downloaded
                for fx in fixtures:
                    # Check if there's a dismissed marker
                    ws = await s.get(RugbyWantedState, fx.id)
                    if ws and ws.dismissed:
                        continue

                    # Check if fixture is matched to auto/confirmed and media is
                    # queued/downloading/downloaded
                    match = (
                        await s.execute(
                            select(RugbyMatch).where(
                                and_(
                                    RugbyMatch.fixture_id == fx.id,
                                    RugbyMatch.status.in_(["auto", "confirmed"]),
                                )
                            )
                        )
                    ).scalar_one_or_none()

                    if match and match.media_id:
                        item = await s.get(MediaItem, match.media_id)
                        if item and item.status in [
                            MediaStatus.DOWNLOADED,
                            MediaStatus.DOWNLOADING,
                            MediaStatus.QUEUED,
                            MediaStatus.PENDING,
                        ]:
                            continue

                    # Fixture is wanted
                    if fx.date:
                        # Ensure both datetimes are timezone-aware
                        fx_date = fx.date if fx.date.tzinfo else fx.date.replace(tzinfo=timezone.utc)
                        days_missing = (now - fx_date).days
                    else:
                        days_missing = None
                    state = "missing"
                    if ws:
                        if ws.gave_up:
                            state = "not_found"
                        elif ws.last_searched_at:
                            state = "searching"

                    league = await s.get(RugbyLeague, fx.league_id)
                    wanted.append(
                        {
                            "fixture_id": fx.id,
                            "league": league.name if league else None,
                            "season": fx.season,
                            "round": fx.round,
                            "home": fx.home_name,
                            "away": fx.away_name,
                            "date": fx.date.isoformat() if fx.date else None,
                            "days_missing": days_missing,
                            "last_searched_at": (
                                ws.last_searched_at.isoformat()
                                if ws and ws.last_searched_at
                                else None
                            ),
                            "attempts": ws.attempts if ws else 0,
                            "state": state,
                            "subscription_id": rugby_sub.subscription_id,
                        }
                    )

        return wanted

    async def _context(self, s, fixture_id: int, subscription_id: Optional[int] = None):
        """Fixture + the core subscription that follows its league."""
        fx = await s.get(RugbyFixture, fixture_id)
        if fx is None:
            raise LookupError(f"Fixture {fixture_id} not found")
        q = select(RugbySubscription).where(RugbySubscription.league_id == fx.league_id)
        if subscription_id:
            q = q.where(RugbySubscription.subscription_id == subscription_id)
        rs = (await s.execute(q)).scalars().first()
        if rs is None:
            raise LookupError("No subscription follows this league")
        return fx, await s.get(Subscription, rs.subscription_id)

    def _tg(self):
        tg = self.ctx.tg_service
        if tg is None or getattr(tg, "client", None) is None:
            raise RuntimeError("Telegram is not connected")
        return tg

    async def search_fixture(self, fixture_id: int, subscription_id: Optional[int] = None) -> list[dict]:
        """Search the followed channel/topic for either team; score each video
        against THIS fixture. Sorted by confidence, best first."""
        from app.rugby import matcher
        from app.sync.engine import sub_dtos

        tg = self._tg()
        async with self.ctx.session() as s:
            fx, sub = await self._context(s, fixture_id, subscription_id)
            chan_dto, topic_dto = await sub_dtos(s, sub)
            fxd = {"id": fx.id, "home_name": fx.home_name, "away_name": fx.away_name, "date": fx.date,
                   "season": fx.season, "round": fx.round, "league_id": fx.league_id}
            seen: dict[int, dict] = {}
            # Normalized names ("Bath Rugby" -> "bath") match how posts title games.
            for term in filter(None, (matcher.normalize(n) for n in (fx.home_name, fx.away_name) if n)):
                async for dto in tg.iter_media(chan_dto, topic_dto, search=term, limit=50):
                    if dto.tg_msg_id in seen:
                        continue
                    text = " ".join(filter(None, (dto.file_name, dto.caption)))
                    _, conf, status = matcher.match(text, dto.date_posted, [fxd])
                    tracked = (await s.execute(select(MediaItem).where(
                        MediaItem.channel_id == sub.channel_id, MediaItem.tg_msg_id == dto.tg_msg_id))).scalar_one_or_none()
                    seen[dto.tg_msg_id] = {
                        "channel_id": sub.channel_id, "tg_msg_id": dto.tg_msg_id,
                        "file_name": dto.file_name, "caption": (dto.caption or "")[:200],
                        "size_bytes": dto.size_bytes,
                        "date": dto.date_posted.isoformat() if dto.date_posted else None,
                        "confidence": round(conf, 3), "auto": status == "auto",
                        "already_tracked": tracked is not None,
                        "media_id": tracked.id if tracked else None,
                        "media_status": tracked.status if tracked else None,
                    }
        ws = await self._state(fixture_id)
        await self._update_state(fixture_id, attempts=(ws.attempts or 0) + 1 if ws else 1,
                                 last_searched_at=datetime.now(timezone.utc))
        return sorted(seen.values(), key=lambda c: -c["confidence"])

    async def _state(self, fixture_id: int):
        async with self.ctx.session() as s:
            return await s.get(RugbyWantedState, fixture_id)

    async def grab_fixture(self, fixture_id: int, channel_id: int, tg_msg_id: int) -> dict:
        """Queue a message for download as this fixture's video and confirm the match.
        A message already tracked (skipped, failed, needs review) is requeued instead."""
        from app.db.repositories import media as media_repo
        from app.sync.engine import sub_dtos

        async with self.ctx.session() as s:
            fx, sub = await self._context(s, fixture_id)
            item = (await s.execute(select(MediaItem).where(
                MediaItem.channel_id == channel_id, MediaItem.tg_msg_id == tg_msg_id))).scalar_one_or_none()
            if item is None:
                chan_dto, _ = await sub_dtos(s, sub)
                dto = await self._tg().get_message(chan_dto, tg_msg_id)
                if dto is None:
                    raise LookupError("Message not found or has no video")
                item = await media_repo.upsert_from_tg_dto(s, dto, sub.id, channel_id, sub.topic_id)
            if item.status not in (MediaStatus.DOWNLOADED, MediaStatus.DOWNLOADING):
                item.status = MediaStatus.PENDING
                item.skip_reason = None
            item.subscription_id = item.subscription_id or sub.id
            item.content_date = fx.date or item.content_date
            match = (await s.execute(select(RugbyMatch).where(RugbyMatch.media_id == item.id))).scalar_one_or_none()
            if match is None:
                match = RugbyMatch(media_id=item.id)
                s.add(match)
            match.fixture_id, match.league_id = fx.id, fx.league_id
            match.season, match.round = fx.season, fx.round
            match.home_name, match.away_name = fx.home_name, fx.away_name
            match.status, match.confidence = "confirmed", 1.0
            await s.commit()
            return {"media_id": item.id, "status": str(item.status), "fixture_id": fixture_id}

    async def dismiss_fixture(self, fixture_id: int) -> None:
        """Mark a fixture as dismissed in wanted list."""
        await self._update_state(fixture_id, dismissed=True)

    async def _update_state(
        self,
        fixture_id: int,
        last_searched_at: Optional[datetime] = None,
        attempts: Optional[int] = None,
        gave_up: Optional[bool] = None,
        dismissed: Optional[bool] = None,
    ) -> None:
        """Update RugbyWantedState for a fixture."""
        async with self.ctx.session() as s:
            ws = await s.get(RugbyWantedState, fixture_id)
            if ws is None:
                ws = RugbyWantedState(fixture_id=fixture_id)
                s.add(ws)

            if last_searched_at is not None:
                ws.last_searched_at = last_searched_at
            if attempts is not None:
                ws.attempts = attempts
            if gave_up is not None:
                ws.gave_up = gave_up
            if dismissed is not None:
                ws.dismissed = dismissed

            await s.commit()

    async def run_auto_search(self, now: datetime) -> None:
        """For wanted fixtures missing >24h: search; grab an "auto"-grade match;
        give up after 7 days (state not_found, still manually searchable)."""
        for w in await self.list_wanted():
            if w["state"] == "not_found":
                continue
            played = datetime.fromisoformat(w["date"]) if w.get("date") else None
            if played is not None and played.tzinfo is None:
                played = played.replace(tzinfo=timezone.utc)  # SQLite drops tz
            if played is None or now - played < timedelta(hours=24):
                continue
            if now - played > timedelta(days=7):
                await self._update_state(w["fixture_id"], gave_up=True)
                await self.ctx.log("info", "rugby", f"Gave up looking for {w['home']} vs {w['away']} after 7 days")
                continue
            try:
                cands = await self.search_fixture(w["fixture_id"], w.get("subscription_id"))
            except Exception as e:  # noqa: BLE001 — one bad fixture must not stop the sweep
                await self.ctx.log("warning", "rugby", f"Search failed for {w['home']} vs {w['away']}: {e}")
                continue
            top = next((c for c in cands if c["auto"] and c["media_status"] not in ("downloaded", "downloading")), None)
            if top:
                await self.grab_fixture(w["fixture_id"], top["channel_id"], top["tg_msg_id"])
                await self.ctx.log("success", "rugby", f"Auto-grabbed {w['home']} vs {w['away']}")


async def auto_search_loop(ctx, every: timedelta = timedelta(hours=6)) -> None:
    """Plugin background task: run the wanted sweep every 6 hours."""
    import asyncio
    while True:
        await asyncio.sleep(every.total_seconds())
        try:
            await WantedService(ctx).run_auto_search(datetime.now(timezone.utc))
        except Exception as e:  # noqa: BLE001
            await ctx.log("warning", "rugby", f"Wanted sweep failed: {e}")
