"""Fixture resolution beyond the local DB, and where unmatched media goes.

Order for an item the local fixtures can't auto-file:
  1. date-window sweep — refetch every tracked league's rounds that could hold a
     game within ±WINDOW_DAYS (plus round 0 friendlies and the next round, so a
     new season or a late-added tour game shows up);
  2. team search — searchevents "Home_vs_Away", any league in the catalog.
Topic history (which league a topic's matched videos landed in) is the prior
for scoring and the folder for anything still unmatched.
"""

import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import MediaItem
from app.rugby import matcher
from app.rugby.api import RugbyApiError
from app.rugby.models import RugbyFixture, RugbyLeague, RugbyMatch
from app.sync.naming import safe_segment

WINDOW_DAYS = 3
PRIOR_MIN, PRIOR_SHARE = 3, 0.7
# ponytail: per-process TTL cache of fetched rounds; persist it if restarts
# during big backfills start re-hitting the API.
_FETCH_TTL = 6 * 3600

# Library folder names for leagues whose thesportsdb name differs from the
# user's. Overridable via plugin config "league_names" {"<id>": "<name>"}.
DEFAULT_LEAGUE_NAMES = {
    4414: "Gallagher Premiership",
    4986: "The Rugby Championship",
    4446: "URC",
    4430: "Top 14",
    4714: "Six Nations",
}
_league_names = dict(DEFAULT_LEAGUE_NAMES)


def configure(config: dict | None) -> None:
    """Apply config overrides (called on enable)."""
    _league_names.clear()
    _league_names.update(DEFAULT_LEAGUE_NAMES)
    for k, v in ((config or {}).get("league_names") or {}).items():
        if str(k).isdigit() and v:
            _league_names[int(k)] = str(v)


def league_title(league) -> str:
    """Display/folder name for a league row (None -> "Rugby")."""
    if league is None:
        return "Rugby"
    return _league_names.get(league.id) or league.name


def season_start(d: datetime, split: bool) -> int:
    """Season folder year for a date: split-year seasons start in July."""
    return d.year - 1 if split and d.month < 7 else d.year


def _as_utc(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def split_leagues(s) -> set[int]:
    """League ids whose seasons are split-year ("2025-2026")."""
    return set((await s.execute(
        select(RugbyFixture.league_id).where(RugbyFixture.season.like("%-%"))
        .distinct())).scalars().all())


async def topic_prior(s, topic_id) -> int | None:
    """The league a topic's matched videos overwhelmingly belong to, if any."""
    if not topic_id:
        return None
    rows = (await s.execute(
        select(RugbyMatch.league_id, func.count())
        .join(MediaItem, MediaItem.id == RugbyMatch.media_id)
        .where(MediaItem.topic_id == topic_id,
               RugbyMatch.status.in_(("auto", "confirmed")),
               RugbyMatch.league_id.is_not(None))
        .group_by(RugbyMatch.league_id))).all()
    total = sum(n for _lid, n in rows)
    if total < PRIOR_MIN:
        return None
    lid, n = max(rows, key=lambda r: r[1])
    return lid if n / total >= PRIOR_SHARE else None


class Resolver:
    """API lookups for one service; remembers what it fetched recently."""

    def __init__(self, svc):
        self.svc = svc
        self._fetched: dict[tuple, float] = {}

    def _fresh(self, key) -> bool:
        """True if key was fetched within the TTL; else marks it fetched now."""
        now = time.monotonic()
        if now - self._fetched.get(key, -_FETCH_TTL - 1) < _FETCH_TTL:
            return True
        self._fetched[key] = now
        return False

    async def _round_keys(self, when: datetime) -> list[tuple[int, str, int]]:
        lo = when - timedelta(days=WINDOW_DAYS)
        hi = when + timedelta(days=WINDOW_DAYS)
        async with self.svc.ctx.session() as s:
            tracked = (await s.execute(select(RugbyLeague.id).where(
                RugbyLeague.tracked.is_(True)))).scalars().all()
            split = await split_leagues(s)
            has_fixtures = set((await s.execute(
                select(RugbyFixture.league_id).distinct())).scalars().all())
            recent = (await s.execute(
                select(RugbyFixture.league_id, RugbyFixture.season,
                       RugbyFixture.round, RugbyFixture.date)
                .where(RugbyFixture.date >= lo - timedelta(days=21),
                       RugbyFixture.date <= hi))).all()
        keys: set[tuple[int, str, int]] = set()
        last: dict[tuple[int, str], int] = {}
        for lid, ssn, rnd, d in recent:
            if lid not in tracked or not (rnd or "").isdigit():
                continue
            r = int(rnd)
            if r < 100:  # sparse playoff numbers have no "next round"
                last[(lid, ssn)] = max(last.get((lid, ssn), 0), r)
            if d is not None and lo <= _as_utc(d) <= hi:
                keys.add((lid, ssn, r))
        for (lid, ssn), r in last.items():
            keys.add((lid, ssn, r + 1))  # the round after the last one we know
        for lid in tracked:
            y = season_start(when, True)
            # Unknown convention (no fixtures yet): probe both formats.
            formats = ([f"{y}-{y + 1}"] if lid in split else
                       [str(when.year)] if lid in has_fixtures else
                       [f"{y}-{y + 1}", str(when.year)])
            for ssn in formats:
                keys.add((lid, ssn, 0))  # friendlies / tours / one-offs
                if (lid, ssn) not in last:
                    keys.add((lid, ssn, 1))  # season not fetched yet
        return sorted(keys)

    async def sweep(self, when: datetime | None) -> bool:
        """Refresh rounds near `when` across tracked leagues. True if any
        fixture landed."""
        if when is None:
            return False
        landed = False
        for lid, ssn, rnd in await self._round_keys(_as_utc(when)):
            if self._fresh(("round", lid, ssn, rnd)):
                continue
            try:
                evs = await self.svc.api.fetch_round(lid, rnd, ssn)
            except RugbyApiError:
                continue
            landed |= await self._store(evs, {lid}, default=lid)
        return landed

    async def search(self, text: str) -> bool:
        """searchevents by team names; stores hits in catalogued leagues."""
        teams = matcher.split_teams(text)
        search = getattr(self.svc.api, "search_events", None)
        if not teams or search is None:
            return False
        query = "_vs_".join(t.replace(" ", "_") for t in teams)
        if self._fresh(("search", query.lower())):
            return False
        try:
            evs = await search(query)
        except RugbyApiError:
            return False
        async with self.svc.ctx.session() as s:
            known = set((await s.execute(select(RugbyLeague.id))).scalars().all())
        return await self._store(
            [e for e in evs if (e.get("strSport") or "Rugby") == "Rugby"], known)

    async def _store(self, evs, leagues: set[int], default=None) -> bool:
        rows = [(int(e["idLeague"]) if e.get("idLeague") else default, e)
                for e in evs or [] if e.get("idEvent")]
        rows = [(lid, e) for lid, e in rows if lid in leagues]
        if not rows:
            return False
        async with self.svc.ctx.session() as s:
            for lid, ev in rows:
                await self.svc._upsert_fixture(s, lid, ev)
            await s.commit()
        return True


def match_path(league, season, rnd, home, away, ext="") -> str:
    """league/Season N/Round NN - Home vs Away.ext. Always a Jellyfin-parsed
    "Season N" folder (a raw "2024-2025" folder is not read as a season)."""
    rnd = (rnd or "").strip()
    year = (season or "")[:4]
    label = f"Round {int(rnd):02d}" if rnd.isdigit() else (rnd or "Match")
    return "/".join([safe_segment(league or "Rugby"),
                     f"Season {int(year) if year.isdigit() else 1}",
                     safe_segment(f"{label} - {home} vs {away}{ext}")])


async def fallback_path(svc, item, ext: str = "") -> str | None:
    """League/Season folder for an item with no auto/confirmed match, taken
    from its topic's history. None when the topic has no dominant league."""
    async with svc.ctx.session() as s:
        lid = await topic_prior(s, getattr(item, "topic_id", None))
        league = await s.get(RugbyLeague, lid) if lid else None
        if league is None:
            return None
        split = lid in await split_leagues(s)
    name = item.file_name or f"{item.id}{ext}"
    when = matcher.title_date(name, item.date_posted) or item.date_posted
    year = season_start(_as_utc(when), split)
    return "/".join([safe_segment(league_title(league)), f"Season {year}",
                     safe_segment(name)])
