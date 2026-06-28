"""Rugby service: orchestrates scrape/API fetch, matching, and naming tokens.

All DB access goes through the injected PluginContext session. The API client is
injectable so the service can be tested without network.
"""

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from sqlalchemy import func, select

from app.db.models import MediaItem, Topic
from app.rugby import matcher, scraper
from app.rugby.api import RugbyApi, RugbyApiError
from app.rugby.models import (
    RugbyFixture, RugbyLeague, RugbyMatch, RugbySubscription, RugbyTeam,
)


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

    # ---- matching -------------------------------------------------------
    async def match_item(self, item):
        """Match a freshly discovered item to a fixture (uses its subscription)."""
        sub_id = getattr(item, "subscription_id", None)
        if not sub_id:
            return None
        text = item.file_name or item.caption or ""
        async with self.ctx.session() as s:
            league_id = await self._league_for_sub(s, sub_id)
            if league_id is None:
                return None

            async def _load():
                rows = (await s.execute(
                    select(RugbyFixture).where(RugbyFixture.league_id == league_id)
                )).scalars().all()
                return [{"id": f.id, "home_name": f.home_name,
                         "away_name": f.away_name, "date": f.date,
                         "season": f.season, "round": f.round} for f in rows]

            fixtures = await _load()
            best, conf, status = matcher.match(text, item.date_posted, fixtures)
            if status == "none":
                # Incremental: try one targeted lookup, then re-match.
                if await self._ondemand_fetch(text, item.date_posted):
                    fixtures = await _load()
                    best, conf, status = matcher.match(text, item.date_posted, fixtures)
                if status == "none":
                    return None
            rm = (await s.execute(
                select(RugbyMatch).where(RugbyMatch.media_id == item.id)
            )).scalar_one_or_none()
            if rm is None:
                rm = RugbyMatch(media_id=item.id)
                s.add(rm)
            rm.fixture_id = best["id"] if best else None
            rm.league_id = league_id
            rm.season = best["season"] if best else None
            rm.round = best["round"] if best else None
            rm.home_name = best["home_name"] if best else None
            rm.away_name = best["away_name"] if best else None
            rm.confidence = conf
            rm.status = status
            await s.commit()
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

    def _entry_for(self, item, fixtures, by_id, leagues, teams, stored):
        """Build one enrichment entry for a media item, or None if no match.

        A stored rugby_match (auto/confirmed/needs_review) overrides the live
        on-the-fly guess.
        """
        m = stored.get(item.id)
        if m and m.fixture_id and m.fixture_id in by_id:
            fx, status = by_id[m.fixture_id], m.status
        else:
            text = item.file_name or item.caption or ""
            fx, _conf, status = matcher.match(text, item.date_posted, fixtures)
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

    async def _ondemand_fetch(self, text, date) -> bool:
        """Fill one missing fixture with a single targeted round lookup.

        Needs league (title hint) + numeric round to target. Tries the season
        formats implied by the date (≤2 calls), deduped so a burst of videos for
        the same game costs one fetch. Returns True if new fixtures landed.
        """
        needle = matcher.league_hint(text or "")
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
        for item in media:
            e = self._entry_for(item, fixtures, by_id, leagues, teams, stored)
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
        for item in media:
            e = self._entry_for(item, fixtures, by_id, leagues, teams, stored)
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
                     "date": f.date, "season": f.season, "round": f.round} for f in rows]
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

    # ---- jellyfin (rich NFO with team actors + poster) -----------------
    async def write_jellyfin(self, item, path):
        """Write a rich episodedetails .nfo (teams as actors) + poster.jpg."""
        try:
            async with self.ctx.session() as s:
                m = (await s.execute(
                    select(RugbyMatch).where(RugbyMatch.media_id == item.id)
                )).scalar_one_or_none()
                if not m or m.status not in ("auto", "confirmed"):
                    return
                league = await s.get(RugbyLeague, m.league_id) if m.league_id else None
                fx = await s.get(RugbyFixture, m.fixture_id) if m.fixture_id else None
                home_badge = await self._team_badge(s, fx.home_team_id) if fx else None
                away_badge = await self._team_badge(s, fx.away_team_id) if fx else None
            aired = item.date_posted.date().isoformat() if item.date_posted else ""
            nfo = _build_episode_nfo(m, fx, league, home_badge, away_badge, aired)
            Path(path).with_suffix(".nfo").write_text(nfo, encoding="utf-8")
            if home_badge:
                await scraper.download_logo(home_badge, str(Path(path).parent / "poster.jpg"))
        except Exception as ex:  # noqa: BLE001 - artwork is best-effort
            await self.ctx.log("warning", "rugby", f"Jellyfin write failed: {ex}")

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
            return _match_dict(m)

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


def _build_episode_nfo(match, fixture, league, home_badge, away_badge, aired) -> str:
    """Kodi/Jellyfin episodedetails with the two teams as <actor> (badge=thumb)."""
    home = match.home_name or ""
    away = match.away_name or ""
    league_name = league.name if league else ""
    score = ""
    venue = ""
    if fixture:
        if fixture.home_score is not None and fixture.away_score is not None:
            score = f"{fixture.home_score}-{fixture.away_score} "
        venue = f"at {fixture.venue} " if fixture.venue else ""
    plot = f"{score}{venue}{league_name} {match.season or ''} Round {match.round or ''}".strip()
    season_int = int(match.season[:4]) if (match.season or "")[:4].isdigit() else 1
    episode_int = int(match.round) if (match.round or "").isdigit() else 1

    actors = ""
    for name, role, thumb in ((home, "Home", home_badge), (away, "Away", away_badge)):
        actors += (f"  <actor>\n    <name>{escape(name)}</name>\n"
                   f"    <role>{role}</role>\n    <type>Actor</type>\n")
        if thumb:
            actors += f"    <thumb>{escape(thumb)}</thumb>\n"
        actors += "  </actor>\n"

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<episodedetails>\n'
        f"  <title>{escape(f'{home} vs {away}')}</title>\n"
        f"  <showtitle>{escape(league_name)}</showtitle>\n"
        f"  <season>{season_int}</season>\n  <episode>{episode_int}</episode>\n"
        f"  <plot>{escape(plot)}</plot>\n  <aired>{aired}</aired>\n"
        f"  <studio>{escape(league_name)}</studio>\n  <genre>Rugby</genre>\n"
        f"{actors}</episodedetails>\n"
    )


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
