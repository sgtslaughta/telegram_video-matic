"""Rugby service: orchestrates scrape/API fetch, matching, and naming tokens.

All DB access goes through the injected PluginContext session. The API client is
injectable so the service can be tested without network.
"""

import asyncio
import shutil
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from sqlalchemy import func, select

from app.db.models import Channel, MediaItem, Subscription, Topic
from app.rugby import matcher, scraper
from app.rugby.api import RugbyApi, RugbyApiError
from app.rugby.models import (
    RugbyFixture, RugbyLeague, RugbyMatch, RugbySubscription, RugbyTeam,
)
from app.sync.naming import safe_segment


def _sidecar(video: Path, suffix: str) -> Path:
    """Sibling artwork path for a video ("X.mp4", "-thumb.jpg" -> "X-thumb.jpg")."""
    base = video.name[: -len(video.suffix)] if video.suffix else video.name
    return video.parent / f"{base}{suffix}"


def _season_year(season: str) -> int:
    """First 4-digit year of a season string ("2024-2025" -> 2024); 1 if none."""
    s = (season or "").strip()
    return int(s[:4]) if s[:4].isdigit() else 1


def _season_dir(season: str) -> str:
    """Jellyfin season folder name for a thesportsdb season string."""
    return f"Season {_season_year(season)}"


def _first_sentences(text: str, max_len: int = 400) -> str:
    """First sentence(s) of a bio, capped near max_len at a sentence boundary."""
    text = " ".join((text or "").split())
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    dot = cut.rfind(". ")
    return (cut[:dot + 1] if dot > 0 else cut.rstrip()) + " …"


# Round-by-round scan bounds (covers regular season + a few playoff rounds).
# ponytail: linear scan with early-stop; raise _ROUND_SCAN if a league runs longer.
_ROUND_SCAN = 26
_EMPTY_BREAK = 3
# Circuit breaker: after this many consecutive request failures, stop scanning
# the league (a hard rate-limit block) instead of grinding every round.
_MAX_CONSEC_ERRORS = 5
# thesportsdb numbers playoffs sparsely (≈150=semi, 200=final); sweep them
# explicitly since the linear scan stops at _ROUND_SCAN.
_PLAYOFF_ROUNDS = (125, 150, 160, 170, 180, 190, 200)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _event_datetime(ev):
    """Kick-off datetime of a fixture: prefer the full strTimestamp, else
    combine dateEvent + strTime (upload time can be hours/days later)."""
    ts = ev.get("strTimestamp")
    if ts:
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    date, t = ev.get("dateEvent"), ev.get("strTime")
    if not date:
        return None
    try:
        d = datetime.fromisoformat(f"{date} {t}" if t else date)
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d
    except (ValueError, TypeError):
        return _parse_date(date)


class RugbyService:
    def __init__(self, ctx, api=None):
        self.ctx = ctx
        cfg = getattr(ctx, "config", {}) or {}
        self.api = api or RugbyApi(
            api_key=cfg.get("api_key", "123"),
            min_interval=cfg.get("min_interval", 2.0),
        )
        # (league_id, season, round) tuples already fetched on-demand — avoids
        # re-fetching the same round for every video of that game.
        self._ondemand_seen: set = set()
        # league_id -> enrichment dict (poster/desc/fanart/...), one API lookup
        # per league reused across every file of that league.
        self._league_meta: dict[int, dict] = {}
        # team_id -> {"bio": str} (SportsDB description), one lookup per team.
        self._team_meta: dict[int, dict] = {}

    # ---- catalog (shallow) ---------------------------------------------
    async def refresh_catalog(self):
        """Scrape the league catalog; fall back to the bundled seed on failure."""
        try:
            leagues = await scraper.fetch_league_catalog()
        except Exception as ex:  # noqa: BLE001 - scrape is best-effort
            await self.ctx.log("warning", "rugby",
                               f"Catalog scrape failed, using seed: {ex}")
            leagues = []
        # Empty (page changed / parser missed / network blocked) is as good as a
        # failure — fall back to the bundled seed so the catalog is never empty.
        if not leagues:
            leagues = scraper.load_seed()
        async with self.ctx.session() as s:
            for row in leagues:
                league = await s.get(RugbyLeague, row["id"])
                if league is None:
                    league = RugbyLeague(id=row["id"])
                    s.add(league)
                league.slug = row.get("slug") or league.slug
                league.name = row.get("name") or league.name
                league.category = row.get("category")
            await s.commit()
        self.ctx.set_status({"leagues": len(leagues),
                             "last_catalog_refresh": datetime.now(timezone.utc).isoformat()})
        return len(leagues)

    def _merge_status(self, **kw):
        """Update the published health.status, preserving existing keys."""
        st = dict(self.ctx.health.get("status") or {})
        st.update(kw)
        self.ctx.set_status(st)

    # ---- deep fetch (fixtures + teams for one league) ------------------
    async def deep_fetch(self, league_id: int, season: str | None = None,
                         _batch: bool = False):
        """Pull a league's fixtures (and the teams they reference) from the API.

        _batch=True means a caller (rescan) owns the overall sync progress, so
        we don't reset the syncing flags here.
        """
        if not _batch:
            self._merge_status(syncing=True, sync_total=1, sync_done=0,
                               sync_current=str(league_id))
        try:
            # eventsseason truncates to 15 rows on the free tier (rounds 1-3
            # only), so scan round-by-round instead (uncapped) + pastleague for
            # finals. search_all_seasons is also stale, so target current+prev.
            seasons = [season] if season else _recent_seasons()
            team_ids: set[int] = set()
            league_badge = None
            seen: set[int] = set()
            errors = 0
            consec = 0
            broke = False
            async with self.ctx.session() as s:
                async def _apply(ev):
                    nonlocal league_badge
                    # Dedup: the playoff sweep (r200) and pastleague return the
                    # same final; a second add of the same PK aborts the txn.
                    fid = int(ev["idEvent"]) if ev.get("idEvent") else None
                    if fid is None or fid in seen:
                        return
                    seen.add(fid)
                    await self._upsert_fixture(s, league_id, ev)
                    league_badge = league_badge or ev.get("strLeagueBadge")
                    for k in ("idHomeTeam", "idAwayTeam"):
                        if ev.get(k):
                            team_ids.add(int(ev[k]))

                async def _safe_round(rnd, ssn):
                    # A transient error on one round must not abort the league;
                    # skip it and keep whatever else succeeds, but count it so a
                    # rate-limited fetch surfaces instead of looking empty.
                    nonlocal errors, consec
                    try:
                        r = await self.api.fetch_round(league_id, rnd, ssn)
                        consec = 0
                        return r
                    except RugbyApiError:
                        errors += 1
                        consec += 1
                        return []

                for ssn in seasons:
                    empty = 0
                    for rnd in range(1, _ROUND_SCAN + 1):
                        if consec >= _MAX_CONSEC_ERRORS:
                            broke = True
                            break  # hard block — stop hammering
                        evs = await _safe_round(rnd, ssn)
                        if not evs:
                            empty += 1
                            if empty >= _EMPTY_BREAK and rnd > 3:
                                break  # season exhausted; stop scanning
                            continue
                        empty = 0
                        for ev in evs:
                            await _apply(ev)
                    if not broke:
                        for rnd in _PLAYOFF_ROUNDS:  # semis/finals (sparse)
                            for ev in await _safe_round(rnd, ssn):
                                await _apply(ev)
                    await s.commit()  # persist each season as it completes
                    if broke:
                        break
                # Finals/playoffs use sparse round numbers the scan misses.
                if not broke:
                    try:
                        for ev in await self.api.fetch_past_league(league_id):
                            await _apply(ev)
                    except RugbyApiError:
                        errors += 1
                await s.commit()
            for tid in team_ids:
                await self._fetch_team(tid, league_id)
            async with self.ctx.session() as s:
                league = await s.get(RugbyLeague, league_id)
                if league:
                    league.tracked = True
                    league.badge_url = league.badge_url or league_badge
                    league.last_deep_fetch_at = datetime.now(timezone.utc)
                    await s.commit()
                    self._merge_status(sync_current=league.name)
            status = dict(self.ctx.health.get("status") or {})
            if errors:
                # Rate-limit / transient: amber indicator, not a hard red error.
                status["rate_limited"] = True
                self.ctx.set_status(status)
                await self.ctx.log(
                    "info", "rugby",
                    f"League {league_id}: {errors} request(s) rate-limited; "
                    f"coverage may be incomplete — use 'Scan now' to retry.")
            else:
                status["rate_limited"] = False
                self.ctx.set_status(status)
                self.ctx.clear_error()
        except RugbyApiError as ex:
            await self.ctx.log("error", "rugby",
                               f"Deep fetch failed for league {league_id}: {ex.detail}")
            raise
        finally:
            if not _batch:
                self._merge_status(syncing=False, sync_done=1)

    async def _upsert_fixture(self, s, league_id, ev):
        fid = int(ev["idEvent"])
        fx = await s.get(RugbyFixture, fid)
        if fx is None:
            fx = RugbyFixture(id=fid)
            s.add(fx)
        fx.league_id = league_id
        fx.season = ev.get("strSeason") or ""
        fx.round = str(ev.get("intRound") or "")
        fx.date = _event_datetime(ev)
        fx.home_team_id = int(ev["idHomeTeam"]) if ev.get("idHomeTeam") else None
        fx.away_team_id = int(ev["idAwayTeam"]) if ev.get("idAwayTeam") else None
        fx.home_name = ev.get("strHomeTeam")
        fx.away_name = ev.get("strAwayTeam")
        fx.home_score = _to_int(ev.get("intHomeScore"))
        fx.away_score = _to_int(ev.get("intAwayScore"))
        fx.venue = ev.get("strVenue") or None
        fx.country = ev.get("strCountry") or None

    async def _fetch_team(self, team_id, league_id):
        try:
            data = await self.api.lookup_team(team_id)
        except RugbyApiError:
            return
        if not data:
            return
        async with self.ctx.session() as s:
            team = await s.get(RugbyTeam, team_id)
            if team is None:
                team = RugbyTeam(id=team_id)
                s.add(team)
            team.league_id = league_id
            team.name = data.get("strTeam") or team.name or str(team_id)
            team.short_name = data.get("strTeamShort") or None
            alt = data.get("strTeamAlternate") or ""
            team.alt_names = [a.strip() for a in alt.split(",") if a.strip()] or None
            team.stadium = data.get("strStadium")
            team.country = data.get("strCountry")
            team.badge_url = data.get("strBadge")
            team.logo_url = data.get("strLogo")
            await s.commit()

    # ---- subscription link ---------------------------------------------
    async def _set_link_only(self, sub_id: int, league_id: int | None):
        """Persist (or clear) the sub→league link without fetching."""
        async with self.ctx.session() as s:
            link = await s.get(RugbySubscription, sub_id)
            if league_id is None:
                if link:
                    await s.delete(link)
                    await s.commit()
                return
            if link is None:
                s.add(RugbySubscription(subscription_id=sub_id, league_id=league_id))
            else:
                link.league_id = league_id
            await s.commit()

    async def set_subscription_league(self, sub_id: int, league_id: int | None):
        await self._set_link_only(sub_id, league_id)
        if league_id is not None:
            await self.deep_fetch(league_id)

    async def _league_for_sub(self, s, sub_id):
        link = await s.get(RugbySubscription, sub_id)
        return link.league_id if link else None

    async def get_subscription_league(self, sub_id: int):
        """The league_id linked to a subscription (None if unset). For the editor
        to show the saved value when reopening a subscription."""
        async with self.ctx.session() as s:
            return await self._league_for_sub(s, sub_id)

    @staticmethod
    async def _source_context(s, item) -> str:
        """Topic + channel name for an item — where the competition is named.

        A file called "England v France.mp4" is only identifiable as an U20 game
        by the "JWC" topic it was posted in.
        """
        parts = []
        topic_id = getattr(item, "topic_id", None)
        if topic_id:
            topic = await s.get(Topic, topic_id)
            if topic and topic.title:
                parts.append(topic.title)
        channel_id = getattr(item, "channel_id", None)
        if channel_id:
            ch = await s.get(Channel, channel_id)
            if ch and ch.title:
                parts.append(ch.title)
        return " ".join(parts)

    # ---- matching -------------------------------------------------------
    async def match_item(self, item):
        """Match a freshly discovered item to a fixture (uses its subscription)."""
        sub_id = getattr(item, "subscription_id", None)
        if not sub_id:
            return None
        text = item.file_name or item.caption or ""
        snippet = text[:80]
        fetched = False
        async with self.ctx.session() as s:
            league_id = await self._league_for_sub(s, sub_id)
            if league_id is None:
                return None
            league = await s.get(RugbyLeague, league_id)
            league_name = league.name if league else ""
            context = await self._source_context(s, item)

            names = {lid: nm for lid, nm in (await s.execute(
                select(RugbyLeague.id, RugbyLeague.name))).all()}

            async def _load(ids=None):
                rows = (await s.execute(
                    select(RugbyFixture).where(
                        RugbyFixture.league_id.in_(ids or [league_id]))
                )).scalars().all()
                return [{"id": f.id, "home_name": f.home_name,
                         "away_name": f.away_name, "date": f.date,
                         "season": f.season, "round": f.round,
                         "league_id": f.league_id,
                         "league_name": names.get(f.league_id, league_name)}
                        for f in rows]

            fixtures = await _load()
            best, conf, status = matcher.match(text, item.date_posted, fixtures,
                                               context=context)
            if status == "none":
                # Incremental: try one targeted lookup, then re-match.
                if await self._ondemand_fetch(text, item.date_posted, context):
                    fetched = True
                    fixtures = await _load()
                    best, conf, status = matcher.match(
                        text, item.date_posted, fixtures, context=context)
            if status == "none":
                # A subscription binds one league, but a forum topic often mixes
                # competitions (tour games, friendlies, a cup the topic never
                # names). Widen to every other tracked league — always landing in
                # needs_review, so the narrow binding stays the only path that
                # files anything unattended.
                others = [lid for lid in (await s.execute(
                    select(RugbyLeague.id).where(RugbyLeague.tracked.is_(True))
                )).scalars().all() if lid != league_id]
                if others:
                    alt, alt_conf, alt_status = matcher.match(
                        text, item.date_posted, await _load(others), context=context)
                    if alt_status != "none":
                        best, conf, status = alt, alt_conf, "needs_review"
            if status != "none":
                rm = (await s.execute(
                    select(RugbyMatch).where(RugbyMatch.media_id == item.id)
                )).scalar_one_or_none()
                if rm is None:
                    rm = RugbyMatch(media_id=item.id)
                    s.add(rm)
                rm.fixture_id = best["id"] if best else None
                # The fixture's own league, which the fallback above may have
                # taken from outside the subscription's binding.
                rm.league_id = (best or {}).get("league_id") or league_id
                rm.season = best["season"] if best else None
                rm.round = best["round"] if best else None
                rm.home_name = best["home_name"] if best else None
                rm.away_name = best["away_name"] if best else None
                rm.confidence = conf
                rm.status = status
                await s.commit()
        # Activity log — outside the session block so ctx.log's own session
        # never nests inside this one. Every outcome is surfaced to the feed.
        if fetched:
            await self.ctx.log("info", "rugby",
                               f"On-demand fixture lookup for “{snippet}”",
                               media_id=item.id)
        if status == "none":
            await self.ctx.log("info", "rugby",
                               f"No fixture match for “{snippet}”",
                               media_id=item.id)
            return None
        teams = f"{best['home_name']} vs {best['away_name']}"
        rnd = f" — Round {best['round']}" if best.get("round") else ""
        if status in ("auto", "confirmed"):
            await self.ctx.log("success", "rugby",
                               f"Matched {teams}{rnd} ({conf:.0%})",
                               media_id=item.id)
        else:  # needs_review
            await self.ctx.log("info", "rugby",
                               f"Needs review — {teams}{rnd} ({conf:.0%})",
                               media_id=item.id)
        return status

    # ---- naming tokens (read) ------------------------------------------
    async def naming_tokens(self, media_id: int) -> dict:
        async with self.ctx.session() as s:
            rm = (await s.execute(
                select(RugbyMatch).where(RugbyMatch.media_id == media_id)
            )).scalar_one_or_none()
            if rm is None or rm.status not in ("auto", "confirmed"):
                return {}
            league = await s.get(RugbyLeague, rm.league_id) if rm.league_id else None
            return _clean({
                "rugby_league": league.name if league else "Unknown League",
                "rugby_season": rm.season or "",
                "rugby_round": rm.round or "0",
                "home": rm.home_name or "",
                "away": rm.away_name or "",
                "rugby_sport": (league.sport if league and league.sport else "rugby"),
            })

    async def path_for(self, media_id: int, ext: str = "") -> str | None:
        """Relative path (league/season/Home vs Away.ext) for a matched item, so
        rugby media auto-files into a league/season tree regardless of the
        subscription's rename_template. None unless the match is auto/confirmed."""
        tokens = await self.naming_tokens(media_id)
        if not tokens:
            return None
        home, away = tokens.get("home"), tokens.get("away")
        if not home or not away:
            return None
        league = tokens.get("rugby_league") or "Rugby"
        season = tokens.get("rugby_season") or ""
        rnd = (tokens.get("rugby_round") or "").strip()
        label = f"Round {int(rnd):02d}" if rnd.isdigit() else (rnd or "Match")
        fname = f"{label} - {home} vs {away}{ext}"
        # Always emit a Jellyfin-recognized "Season N" subfolder so the season
        # groups correctly (a raw "2024-2025" folder is not parsed as a season).
        parts = [safe_segment(league), _season_dir(season), safe_segment(fname)]
        return "/".join(parts)


    # ---- browse enrichment + wizard preview ----------------------------
    async def _match_context(self, s):
        """Load fixtures (+league name), leagues, teams, stored matches once.

        ponytail: O(media*fixtures) in-memory fuzzy scan; fine at this scale.
        """
        fx_rows = (await s.execute(select(RugbyFixture))).scalars().all()
        fixtures = [{"id": f.id, "league_id": f.league_id,
                     "home_name": f.home_name, "away_name": f.away_name,
                     "home_team_id": f.home_team_id, "away_team_id": f.away_team_id,
                     "date": f.date, "season": f.season, "round": f.round,
                     "venue": f.venue, "home_score": f.home_score,
                     "away_score": f.away_score} for f in fx_rows]
        league_ids = {f["league_id"] for f in fixtures}
        leagues = {ln.id: ln for ln in (await s.execute(
            select(RugbyLeague).where(RugbyLeague.id.in_(league_ids))
        )).scalars().all()}
        for f in fixtures:  # league hint factor needs the league name
            ln = leagues.get(f["league_id"])
            f["league_name"] = ln.name if ln else None
        teams = {t.id: t for t in (await s.execute(
            select(RugbyTeam).where(RugbyTeam.league_id.in_(league_ids))
        )).scalars().all()}
        stored = {m.media_id: m for m in (await s.execute(
            select(RugbyMatch).where(
                RugbyMatch.status.in_(("auto", "confirmed", "needs_review")))
        )).scalars().all()}
        return fixtures, {f["id"]: f for f in fixtures}, leagues, teams, stored

    @staticmethod
    async def _context_map(s, media) -> dict:
        """media_id -> "topic channel" text, in two queries for the whole page."""
        topic_ids = {m.topic_id for m in media if m.topic_id}
        chan_ids = {m.channel_id for m in media if m.channel_id}
        topics = dict((await s.execute(
            select(Topic.id, Topic.title).where(Topic.id.in_(topic_ids)))).all()
        ) if topic_ids else {}
        chans = dict((await s.execute(
            select(Channel.id, Channel.title).where(Channel.id.in_(chan_ids)))).all()
        ) if chan_ids else {}
        return {m.id: " ".join(p for p in (topics.get(m.topic_id),
                                           chans.get(m.channel_id)) if p)
                for m in media}

    def _entry_for(self, item, fixtures, by_id, leagues, teams, stored,
                   context: str = ""):
        """Build one enrichment entry for a media item, or None if no match.

        A stored rugby_match (auto/confirmed/needs_review) overrides the live
        on-the-fly guess.
        """
        m = stored.get(item.id)
        if m and m.fixture_id and m.fixture_id in by_id:
            fx, status = by_id[m.fixture_id], m.status
        else:
            text = item.file_name or item.caption or ""
            fx, _conf, status = matcher.match(text, item.date_posted, fixtures,
                                              context=context)
            if status == "none" or not fx:
                return None
        return self._fixture_entry(fx, leagues, teams, status)

    @staticmethod
    def _fixture_entry(fx, leagues, teams, status):
        """Build the enrichment payload for a matched fixture, or None."""
        league = leagues.get(fx["league_id"])
        if league is None:
            return None
        home = teams.get(fx.get("home_team_id"))
        away = teams.get(fx.get("away_team_id"))
        return {
            "league": league.name, "league_badge": league.badge_url,
            "season": fx["season"], "round": fx["round"],
            "home": fx["home_name"], "away": fx["away_name"],
            "home_badge": home.badge_url if home else None,
            "away_badge": away.badge_url if away else None,
            "venue": fx.get("venue"),
            "home_score": fx.get("home_score"),
            "away_score": fx.get("away_score"),
            "status": status,
        }

    async def enrich_messages(self, messages: list[dict]) -> dict:
        """Enrich arbitrary LIVE messages (not cached media), keyed by tg_msg_id.

        messages: [{"tg_msg_id": int, "text": str, "date": datetime|None}]
        Matches each against loaded fixtures — so any browsed video lights up
        without being cached first. No API calls (local match only).
        """
        out: dict = {}
        if not messages:
            return out
        async with self.ctx.session() as s:
            fixtures, _by_id, leagues, teams, _stored = await self._match_context(s)
        if not fixtures:
            return out
        for msg in messages:
            fx, _conf, status = matcher.match(
                msg.get("text") or "", msg.get("date"), fixtures)
            if status == "none" or not fx:
                continue
            entry = self._fixture_entry(fx, leagues, teams, status)
            if entry:
                out[msg["tg_msg_id"]] = entry
        return out

    # ---- incremental on-demand single lookup ---------------------------
    @staticmethod
    def _candidate_seasons(d):
        """Likely thesportsdb season ids for a title date — split-year (northern)
        and single-year (southern). Falls back to recent seasons if no date."""
        if d is None:
            return _recent_seasons()
        start = d.year if d.month >= 7 else d.year - 1
        return [f"{start}-{start + 1}", str(d.year)]

    async def _league_for_needle(self, needle):
        async with self.ctx.session() as s:
            for lid, name in (await s.execute(
                    select(RugbyLeague.id, RugbyLeague.name))).all():
                if needle in (name or "").lower():
                    return lid
        return None

    async def _ondemand_fetch(self, text, date, context: str = "") -> bool:
        """Fill one missing fixture with a single targeted round lookup.

        Needs league (title hint) + numeric round to target. Tries the season
        formats implied by the date (≤2 calls), deduped so a burst of videos for
        the same game costs one fetch. Returns True if new fixtures landed.
        """
        # League may only be named by the topic; the round only ever by the title.
        needle = matcher.league_hint(text or "") or matcher.league_hint(context or "")
        rnd = matcher.parse_round(text or "")
        if not needle or rnd is None:
            return False
        league_id = await self._league_for_needle(needle)
        if league_id is None:
            return False
        tdate = matcher.parse_title_date(text or "") or date
        keys = [(league_id, ssn, rnd) for ssn in self._candidate_seasons(tdate)]
        if all(k in self._ondemand_seen for k in keys):
            return False
        for key in keys:
            if key in self._ondemand_seen:
                continue
            self._ondemand_seen.add(key)
            _lid, ssn, _rd = key
            try:
                evs = await self.api.fetch_round(league_id, rnd, ssn)
            except RugbyApiError:
                continue
            if evs:
                async with self.ctx.session() as s:
                    for ev in evs:
                        await self._upsert_fixture(s, league_id, ev)
                    await s.commit()
                self._ondemand_seen.update(keys)  # game found; don't retry siblings
                return True
        return False

    async def ondemand_fill(self, messages: list[dict]) -> int:
        """For messages with no local fixture, do targeted single lookups."""
        filled = 0
        async with self.ctx.session() as s:
            fixtures, _b, _l, _t, _st = await self._match_context(s)
        for msg in messages:
            text, d = msg.get("text") or "", msg.get("date")
            _fx, _c, status = matcher.match(text, d, fixtures)
            if status != "none":
                continue
            if await self._ondemand_fetch(text, d):
                filled += 1
        return filled

    async def enrichment(self, channel_id) -> dict:
        """Rugby data for a channel's live media, keyed by tg_msg_id (Browse)."""
        out: dict = {}
        async with self.ctx.session() as s:
            fixtures, by_id, leagues, teams, stored = await self._match_context(s)
            if not fixtures:
                return out
            media = (await s.execute(
                select(MediaItem).where(MediaItem.channel_id == channel_id)
            )).scalars().all()
            ctxs = await self._context_map(s, media)
        for item in media:
            e = self._entry_for(item, fixtures, by_id, leagues, teams, stored,
                                ctxs.get(item.id, ""))
            if e:
                out[item.tg_msg_id] = e
        return out

    async def enrichment_by_media(self, media_ids: list[int]) -> dict:
        """Rugby data keyed by media_id (Downloads page, which has no channel)."""
        out: dict = {}
        if not media_ids:
            return out
        async with self.ctx.session() as s:
            fixtures, by_id, leagues, teams, stored = await self._match_context(s)
            if not fixtures:
                return out
            media = (await s.execute(
                select(MediaItem).where(MediaItem.id.in_(media_ids))
            )).scalars().all()
            ctxs = await self._context_map(s, media)
        for item in media:
            e = self._entry_for(item, fixtures, by_id, leagues, teams, stored,
                                ctxs.get(item.id, ""))
            if e:
                out[item.id] = e
        return out

    async def _team_badge(self, s, team_id):
        if not team_id:
            return None
        t = await s.get(RugbyTeam, team_id)
        return t.badge_url if t else None

    # ---- auto-detect leagues from a channel's titles -------------------
    @staticmethod
    def _leagues_for_titles(rows, leagues) -> list[int]:
        """Map title league-hints to catalog league ids."""
        needles = {h for fn, cap in rows
                   if (h := matcher.league_hint(fn or cap or ""))}
        ids: list[int] = []
        for n in needles:
            for lid, name in leagues:
                if n in (name or "").lower():
                    ids.append(lid)
                    break
        return sorted(set(ids))

    async def detect_channel_leagues(self, channel_id) -> list[int]:
        """Leagues referenced by one channel's topic names + cached video titles.

        Forum topics are usually named by competition ("URC", "Six Nations"), so
        topic titles are the strongest, cheapest signal — no message scan needed.
        """
        async with self.ctx.session() as s:
            rows = (await s.execute(
                select(MediaItem.file_name, MediaItem.caption)
                .where(MediaItem.channel_id == channel_id))).all()
            topics = (await s.execute(
                select(Topic.title, Topic.title)
                .where(Topic.channel_id == channel_id))).all()
            leagues = (await s.execute(
                select(RugbyLeague.id, RugbyLeague.name))).all()
        return self._leagues_for_titles(list(rows) + list(topics), leagues)

    async def detect_all_leagues(self) -> list[int]:
        """Leagues referenced across ALL topic names + cached media (every channel)."""
        async with self.ctx.session() as s:
            rows = (await s.execute(
                select(MediaItem.file_name, MediaItem.caption))).all()
            topics = (await s.execute(select(Topic.title, Topic.title))).all()
            leagues = (await s.execute(
                select(RugbyLeague.id, RugbyLeague.name))).all()
        return self._leagues_for_titles(list(rows) + list(topics), leagues)

    async def map_titles_to_leagues(self, titles: list[str]) -> list[int]:
        """Map an arbitrary list of title strings to catalog league ids.

        Used to detect from LIVE Telegram messages (not just cached media_items),
        so leagues only present in un-ingested videos are still found.
        """
        async with self.ctx.session() as s:
            leagues = (await s.execute(
                select(RugbyLeague.id, RugbyLeague.name))).all()
        return self._leagues_for_titles([(t, None) for t in titles], leagues)

    async def deep_fetch_many(self, league_ids: list[int]) -> int:
        """Deep-fetch a list of leagues with a single shared progress bar."""
        ids = sorted(set(league_ids))
        if not ids:
            return 0
        async with self.ctx.session() as s:
            names = {lid: nm for lid, nm in (await s.execute(
                select(RugbyLeague.id, RugbyLeague.name)
                .where(RugbyLeague.id.in_(ids)))).all()}
        self._merge_status(syncing=True, sync_total=len(ids), sync_done=0,
                           sync_current=None)
        try:
            for i, lid in enumerate(ids):
                self._merge_status(sync_current=names.get(lid, str(lid)))
                await self.deep_fetch(lid, _batch=True)
                self._merge_status(sync_done=i + 1)
        finally:
            self._merge_status(syncing=False, sync_current=None)
        return len(ids)

    async def autofetch_leagues(self, league_ids: list[int]) -> list[int]:
        """Deep-fetch the given leagues that aren't already tracked."""
        async with self.ctx.session() as s:
            todo = [lid for lid in dict.fromkeys(league_ids)
                    if (lg := await s.get(RugbyLeague, lid)) and not lg.tracked]
        await self.deep_fetch_many(todo)
        return todo

    async def tracked_league_ids(self) -> list[int]:
        async with self.ctx.session() as s:
            return [r for (r,) in (await s.execute(
                select(RugbyLeague.id).where(RugbyLeague.tracked.is_(True)))).all()]

    async def autofetch_channel(self, channel_id) -> list[int]:
        """Detect a channel's leagues and deep-fetch any not yet loaded."""
        fetched = []
        for lid in await self.detect_channel_leagues(channel_id):
            async with self.ctx.session() as s:
                lg = await s.get(RugbyLeague, lid)
            if lg and lg.tracked:  # already has fixtures
                continue
            await self.deep_fetch(lid)
            fetched.append(lid)
        return fetched

    async def rescan(self) -> int:
        """Manual 'Scan now': refresh the catalog, detect every league referenced
        across ALL media (any channel/topic), and deep-fetch them plus any
        already-tracked league (retrying rounds a prior rate-limit left short).
        The adaptive throttle + circuit breaker keep this from hammering the API.
        """
        await self.refresh_catalog()
        detected = set(await self.detect_all_leagues())
        tracked = set(await self.tracked_league_ids())
        return await self.deep_fetch_many(sorted(detected | tracked))

    async def preview(self, league_id, text, date=None) -> dict:
        """Dry-run match for the subscription wizard (read-only, no writes)."""
        async with self.ctx.session() as s:
            rows = (await s.execute(
                select(RugbyFixture).where(RugbyFixture.league_id == league_id)
            )).scalars().all()
            league = await s.get(RugbyLeague, league_id)
            teams = (await s.execute(
                select(RugbyTeam).where(RugbyTeam.league_id == league_id)
            )).scalars().all()
        fixtures = [{"id": f.id, "home_name": f.home_name, "away_name": f.away_name,
                     "date": f.date, "season": f.season, "round": f.round,
                     "league_name": league.name if league else None} for f in rows]
        best, conf, status = matcher.match(text, date, fixtures)
        res = {"matched": status != "none", "status": status, "confidence": conf,
               "fixtures_count": len(fixtures), "teams_count": len(teams),
               "league": league.name if league else None,
               "league_badge": league.badge_url if league else None}
        if best:
            badge = {t.name: t.badge_url for t in teams}
            res.update({
                "home": best["home_name"], "away": best["away_name"],
                "season": best["season"], "round": best["round"],
                "home_badge": badge.get(best["home_name"]),
                "away_badge": badge.get(best["away_name"]),
                "tokens": {
                    "rugby_league": league.name if league else "",
                    "rugby_season": best["season"] or "",
                    "rugby_round": best["round"] or "0",
                    "home": best["home_name"] or "", "away": best["away_name"] or "",
                    "rugby_sport": (league.sport if league and league.sport else "rugby"),
                },
            })
        return res

    async def _fetch_league_meta(self, league) -> dict:
        """SportsDB league enrichment (poster/fanart/description/…), cached and
        best-effort. Poster falls back to the stored badge so top-level art
        always exists."""
        if not league:
            return {}
        if league.id in self._league_meta:
            return self._league_meta[league.id]
        meta: dict = {}
        try:
            raw = await self.api.lookup_league(league.id)
        except RugbyApiError:
            raw = None
        if raw:
            meta = {
                "poster": raw.get("strPoster"),
                "fanart": raw.get("strFanart"),
                "banner": raw.get("strBanner"),
                "logo": raw.get("strLogo"),
                "badge": raw.get("strBadge"),
                "description": raw.get("strDescriptionEN"),
                "formed": raw.get("intFormedYear"),
                "country": raw.get("strCountry"),
                "website": raw.get("strWebsite"),
                "gender": raw.get("strGender"),
            }
        # DB stores only badge_url; use it whenever the API lacks the image, so
        # artwork still works offline / rate-limited.
        if not meta.get("badge"):
            meta["badge"] = getattr(league, "badge_url", None)
        if not meta.get("poster"):
            meta["poster"] = meta.get("badge")
        if not meta.get("logo"):
            meta["logo"] = meta.get("badge")
        self._league_meta[league.id] = meta
        return meta

    async def _fetch_team_bio(self, team_id) -> str:
        """SportsDB team description (bio), cached, best-effort. Trimmed to a
        couple of sentences so the episode plot stays readable."""
        if not team_id:
            return ""
        if team_id in self._team_meta:
            return self._team_meta[team_id]["bio"]
        bio = ""
        try:
            raw = await self.api.lookup_team(team_id)
        except RugbyApiError:
            raw = None
        if raw:
            bio = _first_sentences(raw.get("strDescriptionEN") or "")
        self._team_meta[team_id] = {"bio": bio}
        return bio

    # ---- jellyfin (rich NFO + tournament/season artwork) ---------------
    async def write_jellyfin(self, item, path) -> bool:
        """Write episodedetails/season/tvshow .nfo plus tournament + season art.
        Returns True if the episode .nfo was written, False if skipped/failed.

        Layout (Jellyfin): league/Season N/<file>. tvshow.nfo + tournament
        poster/fanart/logo live at the league root; season.nfo + a season poster
        live in the Season folder; the episode .nfo sits beside the video.
        """
        try:
            async with self.ctx.session() as s:
                m = (await s.execute(
                    select(RugbyMatch).where(RugbyMatch.media_id == item.id)
                )).scalar_one_or_none()
                if not m or m.status not in ("auto", "confirmed"):
                    return False
                league = await s.get(RugbyLeague, m.league_id) if m.league_id else None
                fx = await s.get(RugbyFixture, m.fixture_id) if m.fixture_id else None
                home_badge = await self._team_badge(s, fx.home_team_id) if fx else None
                away_badge = await self._team_badge(s, fx.away_team_id) if fx else None
                # Slot = this game's 1-based position among its round's fixtures
                # (by kickoff, then id). Disambiguates the episode number so
                # Jellyfin keeps each match distinct instead of merging a round.
                slot = 1
                if fx:
                    sib = (await s.execute(
                        select(RugbyFixture.id)
                        .where(RugbyFixture.league_id == fx.league_id,
                               RugbyFixture.season == fx.season,
                               RugbyFixture.round == fx.round)
                        .order_by(RugbyFixture.date, RugbyFixture.id)
                    )).scalars().all()
                    if fx.id in sib:
                        slot = sib.index(fx.id) + 1
            home_bio = await self._fetch_team_bio(fx.home_team_id) if fx else ""
            away_bio = await self._fetch_team_bio(fx.away_team_id) if fx else ""
            runtime_min = int((item.duration_sec or 0) / 60)
            dateadded = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            nfo = _build_episode_nfo(m, fx, league, home_badge, away_badge,
                                     runtime_min, dateadded, home_bio, away_bio,
                                     slot)
            p = Path(path)
            p.with_suffix(".nfo").write_text(nfo, encoding="utf-8")

            season_dir = p.parent          # league/Season N
            show_root = p.parent.parent     # league root
            tv = show_root / "tvshow.nfo"
            season_nfo = season_dir / "season.nfo"
            need_show = show_root.exists() and not tv.exists()
            need_season = season_dir.exists() and not season_nfo.exists()
            if not (need_show or need_season):
                return True  # episode .nfo written; show/season already present

            meta = await self._fetch_league_meta(league)
            if need_show:
                tv.write_text(_build_tvshow_nfo(league, meta), encoding="utf-8")
                # Tournament artwork at the top level (English Premiership poster
                # -> season -> content, as requested).
                await self._save_art(meta.get("poster"), show_root / "poster.jpg")
                await self._save_art(meta.get("fanart"), show_root / "fanart.jpg")
                await self._save_art(meta.get("banner"), show_root / "banner.jpg")
                await self._save_art(meta.get("logo"), show_root / "logo.png")
            if need_season:
                season_nfo.write_text(
                    _build_season_nfo(m.season, league, meta), encoding="utf-8")
                # Reuse the tournament poster so the season tile has art too.
                await self._save_art(meta.get("poster"), season_dir / "poster.jpg")
            return True
        except Exception as ex:  # noqa: BLE001 - artwork is best-effort
            await self.ctx.log("warning", "rugby", f"Jellyfin write failed: {ex}")
            return False

    @staticmethod
    async def _save_art(url, dest: Path) -> None:
        """Download an image URL to dest if we have a URL and none is there yet."""
        if url and not dest.exists():
            await scraper.download_logo(url, str(dest))

    # ---- reconcile (re-file matched items + refresh metadata) ----------
    async def _refile(self, item, storage_base) -> str | None:
        """Move item.local_path (+ -thumb.jpg sidecar) to path_for's league/
        Season/round location. Drops the stale .nfo (write_jellyfin rewrites it).
        Returns the new path if moved, else None. Updates DB + the item."""
        if not item.local_path:
            return None
        cur = Path(item.local_path)
        ext = cur.suffix or (
            "." + item.file_name.rsplit(".", 1)[-1]
            if item.file_name and "." in item.file_name else "")
        rel = await self.path_for(item.id, ext)
        if not rel:
            return None
        desired = Path(storage_base) / rel
        if cur == desired or not cur.exists():
            return None
        desired.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(shutil.move, str(cur), str(desired))
        thumb = _sidecar(cur, "-thumb.jpg")
        if thumb.exists():
            shutil.move(str(thumb), str(_sidecar(desired, "-thumb.jpg")))
        cur.with_suffix(".nfo").unlink(missing_ok=True)
        _sidecar(cur, "-poster.jpg").unlink(missing_ok=True)
        async with self.ctx.session() as s:
            it = await s.get(MediaItem, item.id)
            if it:
                it.local_path = str(desired)
                await s.commit()
        item.local_path = str(desired)
        try:  # prune the now-empty old dir (skips if art/other files remain)
            cur.parent.rmdir()
        except OSError:
            pass
        return str(desired)

    async def _reconcile_one(self, media_id) -> bool:
        """Re-file + refresh metadata for one matched item. True if moved."""
        async with self.ctx.session() as s:
            m = (await s.execute(
                select(RugbyMatch).where(RugbyMatch.media_id == media_id)
            )).scalar_one_or_none()
            if not m or m.status not in ("auto", "confirmed"):
                return False
            item = await s.get(MediaItem, media_id)
            if not item or not item.local_path:
                return False
            sub = (await s.get(Subscription, item.subscription_id)
                   if item.subscription_id else None)
            storage_base = sub.storage_path if sub else self.ctx.media_root
        moved = await self._refile(item, storage_base)
        await self.write_jellyfin(item, Path(item.local_path))
        return bool(moved)

    async def reconcile(self) -> dict:
        """Re-file every matched (auto/confirmed) rugby item to its league/
        Season/round path and rewrite full metadata. Fixes items whose match
        resolved after download (never moved) and stale metadata from older
        builds. Idempotent: already-correct items are only refreshed."""
        async with self.ctx.session() as s:
            ids = [m.media_id for m in (await s.execute(
                select(RugbyMatch).where(RugbyMatch.status.in_(("auto", "confirmed")))
            )).scalars().all()]
        moved = 0
        for mid in ids:
            try:
                if await self._reconcile_one(mid):
                    moved += 1
            except Exception as ex:  # noqa: BLE001 - best-effort per item
                await self.ctx.log("warning", "rugby", f"reconcile {mid}: {ex}")
        await self.ctx.log("success", "rugby",
                           f"Reconcile: {moved} re-filed, {len(ids)} refreshed")
        return {"total": len(ids), "moved": moved}

    async def rematch(self) -> dict:
        """Retry fixture matching for media that never matched, then file +
        write metadata for whatever lands.

        match_item only ever runs at discovery, so fixtures that arrive later
        (a deep-fetch, a newly tracked league) can never attach on their own —
        this is the catch-up pass. Items already matched or awaiting review are
        left alone; only media with no match row at all is retried.
        """
        async with self.ctx.session() as s:
            items = (await s.execute(
                select(MediaItem)
                .where(MediaItem.id.not_in(select(RugbyMatch.media_id)))
                .where(MediaItem.subscription_id.in_(
                    select(RugbySubscription.subscription_id)))
            )).scalars().all()
        matched = filed = 0
        for item in items:
            try:
                status = await self.match_item(item)
            except Exception as ex:  # noqa: BLE001 - best-effort per item
                await self.ctx.log("warning", "rugby", f"rematch {item.id}: {ex}")
                continue
            if status not in ("auto", "confirmed"):
                continue
            matched += 1
            if item.local_path and await self._reconcile_one(item.id):
                filed += 1
        await self.ctx.log("success", "rugby",
                           f"Re-match: {matched} of {len(items)} unmatched "
                           f"now matched, {filed} re-filed")
        return {"scanned": len(items), "matched": matched, "filed": filed}

    # ---- jellyfin artwork (legacy poster-only helper) ------------------
    async def write_artwork(self, item, path):
        """Save the matched home team's badge as poster.jpg beside the video."""
        try:
            async with self.ctx.session() as s:
                m = (await s.execute(
                    select(RugbyMatch).where(RugbyMatch.media_id == item.id)
                )).scalar_one_or_none()
                if not m or m.status not in ("auto", "confirmed"):
                    return
                badge = None
                if m.home_name:
                    team = (await s.execute(
                        select(RugbyTeam).where(RugbyTeam.name == m.home_name)
                    )).scalar_one_or_none()
                    badge = team.badge_url if team else None
                if not badge and m.league_id:
                    league = await s.get(RugbyLeague, m.league_id)
                    badge = league.badge_url if league else None
            if badge:
                await scraper.download_logo(badge, str(Path(path).parent / "poster.jpg"))
        except Exception as ex:  # noqa: BLE001 - artwork is best-effort
            await self.ctx.log("warning", "rugby", f"Artwork write failed: {ex}")

    # ---- read helpers for the router -----------------------------------
    async def list_leagues(self, tracked=None):
        async with self.ctx.session() as s:
            q = select(RugbyLeague)
            if tracked is not None:
                q = q.where(RugbyLeague.tracked == tracked)
            rows = (await s.execute(q.order_by(RugbyLeague.name))).scalars().all()
            return [{"id": lg.id, "name": lg.name, "slug": lg.slug,
                     "category": lg.category, "tracked": lg.tracked,
                     "badge_url": lg.badge_url} for lg in rows]

    async def list_fixtures(self, league_id, season=None):
        async with self.ctx.session() as s:
            q = select(RugbyFixture).where(RugbyFixture.league_id == league_id)
            if season:
                q = q.where(RugbyFixture.season == season)
            rows = (await s.execute(q.order_by(RugbyFixture.date))).scalars().all()
            return [{"id": f.id, "season": f.season, "round": f.round,
                     "home_name": f.home_name, "away_name": f.away_name,
                     "date": f.date.isoformat() if f.date else None} for f in rows]

    async def list_matches(self, status=None):
        async with self.ctx.session() as s:
            q = select(RugbyMatch)
            if status:
                q = q.where(RugbyMatch.status == status)
            rows = (await s.execute(q)).scalars().all()
            media_ids = [m.media_id for m in rows if m.media_id]
            sources = {}
            if media_ids:
                items = (await s.execute(
                    select(MediaItem).where(MediaItem.id.in_(media_ids)))).scalars().all()
                sources = {it.id: it for it in items}
            return [_match_dict(m, sources.get(m.media_id)) for m in rows]

    async def update_match(self, media_id, status=None, fixture_id=None):
        """Confirm/reject/re-point a match (the review UI). Returns the row dict."""
        async with self.ctx.session() as s:
            m = (await s.execute(
                select(RugbyMatch).where(RugbyMatch.media_id == media_id)
            )).scalar_one_or_none()
            if m is None:
                return None
            if fixture_id is not None:
                fx = await s.get(RugbyFixture, fixture_id)
                if fx:
                    m.fixture_id = fx.id
                    m.league_id = fx.league_id
                    m.season = fx.season
                    m.round = fx.round
                    m.home_name = fx.home_name
                    m.away_name = fx.away_name
            if status is not None:
                m.status = status
            await s.commit()
            result = _match_dict(m)
            newly_filed = m.status in ("auto", "confirmed")
        # Confirming a match after download re-files the video + refreshes
        # metadata (the download-time path_for saw no match yet). Best-effort.
        if newly_filed:
            try:
                await self._reconcile_one(media_id)
            except Exception as ex:  # noqa: BLE001
                await self.ctx.log("warning", "rugby", f"reconcile on confirm: {ex}")
        return result

    async def status_snapshot(self):
        async with self.ctx.session() as s:
            leagues = (await s.execute(
                select(func.count()).select_from(RugbyLeague))).scalar()
            tracked = (await s.execute(
                select(func.count()).select_from(RugbyLeague)
                .where(RugbyLeague.tracked.is_(True)))).scalar()
            review = (await s.execute(
                select(func.count()).select_from(RugbyMatch)
                .where(RugbyMatch.status == "needs_review"))).scalar()
        return {"last_error": self.ctx.health.get("last_error"),
                "status": self.ctx.health.get("status"),
                "leagues": leagues, "tracked": tracked, "needs_review": review}


def _episode_number(match, fixture, slot=1):
    """(episode_int, round_label). Episode number must be UNIQUE per game or
    Jellyfin collapses every match in a round into one episode (round number
    alone collides). Numeric rounds → round*100 + slot, where slot is the
    game's 1-based position within the round; keeps rounds grouped and ordered
    while staying distinct (e.g. Round 2 → 201, 202, 203). Non-numeric rounds
    (finals) are pushed after the regular season, ordered by date then slot."""
    r = (match.round or "").strip()
    if r.isdigit():
        return int(r) * 100 + slot, f"Round {int(r)}"
    base = 90000
    if fixture and fixture.date:
        base += fixture.date.timetuple().tm_yday * 100
    return base + slot, (r or "Match")


def _build_episode_nfo(match, fixture, league, home_badge, away_badge,
                       runtime_min=0, dateadded="", home_bio="", away_bio="",
                       slot=1) -> str:
    """Fully-populated Kodi/Jellyfin episodedetails: ordered by round/date,
    teams as actors, league as show/studio, played date as premiered/aired."""
    home = match.home_name or ""
    away = match.away_name or ""
    league_name = league.name if league else ""
    sport = (league.sport if league and league.sport else "rugby")
    season_int = int(match.season[:4]) if (match.season or "")[:4].isdigit() else 1
    episode_int, label = _episode_number(match, fixture, slot)

    venue = played = ""
    if fixture:
        venue = fixture.venue or ""
        played = fixture.date.date().isoformat() if fixture.date else ""
    title = f"{label}: {home} vs {away}"
    # No scores in metadata (deliberate): describe the matchup, not the result.
    at_venue = f" at {venue}" if venue else ""
    on_date = f" on {played}" if played else ""
    plot = (f"{label} of the {league_name} {match.season or ''} season: "
            f"{home} vs {away}{at_venue}{on_date}.").strip()
    # Team bios from SportsDB appended so the episode description carries the
    # matchup context (no scores).
    if home_bio:
        plot += f"\n\n{home}: {home_bio}"
    if away_bio:
        plot += f"\n\n{away}: {away_bio}"
    sorttitle = f"{episode_int:04d} {home} vs {away}"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<episodedetails>",
        f"  <title>{escape(title)}</title>",
        f"  <originaltitle>{escape(f'{home} vs {away}')}</originaltitle>",
        f"  <showtitle>{escape(league_name)}</showtitle>",
        f"  <season>{season_int}</season>",
        f"  <episode>{episode_int}</episode>",
        f"  <sorttitle>{escape(sorttitle)}</sorttitle>",
        f"  <plot>{escape(plot)}</plot>",
        f"  <outline>{escape(f'{label} - {home} vs {away}')}</outline>",
    ]
    if runtime_min:
        lines.append(f"  <runtime>{int(runtime_min)}</runtime>")
    if played:
        lines.append(f"  <premiered>{played}</premiered>")
        lines.append(f"  <aired>{played}</aired>")
    if dateadded:
        lines.append(f"  <dateadded>{dateadded}</dateadded>")
    if fixture:
        lines.append(f'  <uniqueid type="thesportsdb" default="true">{fixture.id}</uniqueid>')
    lines.append(f"  <studio>{escape(league_name)}</studio>")
    lines.append(f"  <network>{escape(league_name)}</network>")
    lines.append("  <genre>Rugby</genre>")
    lines.append("  <genre>Sport</genre>")
    if sport and sport.lower() not in ("rugby",):
        lines.append(f"  <genre>{escape(sport.title())}</genre>")
    sport_tag = (f"Rugby {sport.title()}"
                 if sport and sport.lower() not in ("rugby", "") else "Rugby")
    _seen = set()
    for tag in ("Rugby", sport_tag, str(season_int), league_name, match.season,
                label, home, away, (fixture.venue if fixture else None),
                (fixture.country if fixture else None)):
        t = str(tag).strip() if tag is not None else ""
        if t and t not in _seen:
            _seen.add(t)
            lines.append(f"  <tag>{escape(t)}</tag>")
    for order, (name, role, thumb) in enumerate(
            ((home, "Home", home_badge), (away, "Away", away_badge)), start=1):
        lines.append("  <actor>")
        lines.append(f"    <name>{escape(name)}</name>")
        lines.append(f"    <role>{role}</role>")
        lines.append(f"    <order>{order}</order>")
        lines.append("    <type>Actor</type>")
        if thumb:
            lines.append(f"    <thumb>{escape(thumb)}</thumb>")
        lines.append("  </actor>")
    # No <lockdata>: leaving items unlocked lets Jellyfin re-read the NFO on
    # every scan, so later fixes (re-match, numbering, artwork) self-propagate.
    # Disable online metadata downloaders on the rugby library to protect these.
    lines.append("</episodedetails>")
    return "\n".join(lines) + "\n"


def _build_tvshow_nfo(league, meta=None) -> str:
    """Series-level tvshow.nfo so the league folder is recognized as a show,
    enriched with SportsDB tournament data (description, formed year, country,
    poster/fanart art)."""
    meta = meta or {}
    name = league.name if league else "Rugby"
    sport = (league.sport if league and league.sport else "rugby")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<tvshow>",
        f"  <title>{escape(name)}</title>",
        f"  <showtitle>{escape(name)}</showtitle>",
    ]
    if meta.get("description"):
        lines.append(f"  <plot>{escape(meta['description'])}</plot>")
        lines.append(f"  <outline>{escape(meta['description'])}</outline>")
    formed = str(meta.get("formed") or "").strip()
    if formed.isdigit():
        lines.append(f"  <premiered>{formed}-01-01</premiered>")
        lines.append(f"  <year>{formed}</year>")
    lines.append(f"  <studio>{escape(name)}</studio>")
    lines.append("  <genre>Rugby</genre>")
    lines.append("  <genre>Sport</genre>")
    if sport and sport.lower() not in ("rugby",):
        lines.append(f"  <genre>{escape(sport.title())}</genre>")
    sport_tag = (f"Rugby {sport.title()}"
                 if sport and sport.lower() not in ("rugby", "") else "Rugby")
    _seen = set()
    for tag in ("Rugby", sport_tag, name, meta.get("country"), meta.get("gender")):
        t = str(tag).strip() if tag else ""
        if t and t not in _seen:
            _seen.add(t)
            lines.append(f"  <tag>{escape(t)}</tag>")
    # Every available artwork URL, tagged with the Jellyfin aspect it maps to so
    # the server pulls each remotely (badge/logo/poster from DB + API). Deduped
    # by URL so a badge reused as poster/logo isn't emitted twice.
    seen_art = set()
    for aspect, url in (("poster", meta.get("poster")),
                        ("banner", meta.get("banner")),
                        ("clearlogo", meta.get("logo")),
                        ("keyart", meta.get("badge"))):
        if url and url not in seen_art:
            seen_art.add(url)
            lines.append(f'  <thumb aspect="{aspect}">{escape(url)}</thumb>')
    if meta.get("fanart") and meta["fanart"] not in seen_art:
        lines.append("  <fanart>")
        lines.append(f"    <thumb>{escape(meta['fanart'])}</thumb>")
        lines.append("  </fanart>")
    if meta.get("website"):
        lines.append(f"  <website>{escape(meta['website'])}</website>")
    if league and league.id:
        lines.append(f'  <uniqueid type="thesportsdb" default="true">{league.id}</uniqueid>')
    lines.append("</tvshow>")
    return "\n".join(lines) + "\n"


def _build_season_nfo(season, league, meta=None) -> str:
    """Season-level season.nfo. seasonnumber matches the "Season N" folder and
    the episodes' <season>, so Jellyfin groups them together."""
    meta = meta or {}
    num = _season_year(season or "")
    name = league.name if league else "Rugby"
    pretty = season or str(num)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<season>",
        f"  <seasonnumber>{num}</seasonnumber>",
        f"  <title>{escape(str(pretty))}</title>",
        f"  <plot>{escape(f'{pretty} season of {name}.')}</plot>",
        f"  <year>{num}</year>",
        "  <tag>Rugby</tag>",
        f"  <tag>{escape(str(num))}</tag>",
        f"  <tag>{escape(name)}</tag>",
    ]
    if meta.get("poster"):
        lines.append(f'  <thumb aspect="poster">{escape(meta["poster"])}</thumb>')
    lines.append("</season>")
    return "\n".join(lines) + "\n"


def _match_dict(m, src=None):
    """Serialize a RugbyMatch. `src` is the source MediaItem (optional) so the
    review UI can show the original message next to the suggested fixture."""
    return {"media_id": m.media_id, "fixture_id": m.fixture_id,
            "league_id": m.league_id, "season": m.season, "round": m.round,
            "home_name": m.home_name, "away_name": m.away_name,
            "confidence": m.confidence, "status": m.status,
            "source_name": src.file_name if src else None,
            "source_caption": src.caption if src else None,
            "source_date": (src.date_posted.isoformat()
                            if src and src.date_posted else None)}


def _current_season():
    # ponytail: rugby seasons span Sep-Jun; cheap heuristic without a clock arg.
    now = datetime.now(timezone.utc)
    start = now.year if now.month >= 7 else now.year - 1
    return f"{start}-{start + 1}"


def _recent_seasons():
    """Recent season identifiers to scan, in BOTH formats.

    Northern-hemisphere leagues (PREM, Top 14, URC) use split-year "YYYY-YYYY";
    southern-hemisphere ones (Super Rugby, Currie Cup, Rugby Championship) and
    most international tournaments use single-year "YYYY". We don't know a
    league's convention up front, so emit both — the round scan's empty-break
    discards the wrong format after ~3 cheap calls.
    """
    now = datetime.now(timezone.utc)
    start = now.year if now.month >= 7 else now.year - 1
    split = [f"{start}-{start + 1}", f"{start - 1}-{start}"]
    single = [str(now.year), str(now.year - 1)]
    # dedup while preserving order (split first: most of our leagues are northern)
    return list(dict.fromkeys(split + single))


def _to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _clean(tokens: dict) -> dict:
    # Filesystem-hostile characters in team/league names would break paths.
    bad = '/\\:*?"<>|'
    return {k: ("".join(c for c in str(v) if c not in bad).strip() if isinstance(v, str) else v)
            for k, v in tokens.items()}
