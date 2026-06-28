"""Rugby service: orchestrates scrape/API fetch, matching, and naming tokens.

All DB access goes through the injected PluginContext session. The API client is
injectable so the service can be tested without network.
"""

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from sqlalchemy import func, select

from app.db.models import MediaItem
from app.rugby import matcher, scraper
from app.rugby.api import RugbyApi, RugbyApiError
from app.rugby.models import (
    RugbyFixture, RugbyLeague, RugbyMatch, RugbySubscription, RugbyTeam,
)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


class RugbyService:
    def __init__(self, ctx, api=None):
        self.ctx = ctx
        cfg = getattr(ctx, "config", {}) or {}
        self.api = api or RugbyApi(
            api_key=cfg.get("api_key", "123"),
            min_interval=cfg.get("min_interval", 2.0),
        )

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

    # ---- deep fetch (fixtures + teams for one league) ------------------
    async def deep_fetch(self, league_id: int, season: str | None = None):
        """Pull a league's fixtures (and the teams they reference) from the API."""
        try:
            # Free-tier search_all_seasons returns only OLD seasons (truncated), so
            # default to the locally-computed current + previous season instead —
            # eventsseason serves the current season fine by id.
            seasons = [season] if season else _recent_seasons()
            team_ids: set[int] = set()
            league_badge = None
            async with self.ctx.session() as s:
                for ssn in seasons:
                    for ev in await self.api.fetch_season(league_id, ssn):
                        await self._upsert_fixture(s, league_id, ev)
                        league_badge = league_badge or ev.get("strLeagueBadge")
                        for k in ("idHomeTeam", "idAwayTeam"):
                            if ev.get(k):
                                team_ids.add(int(ev[k]))
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
            self.ctx.clear_error()
        except RugbyApiError as ex:
            await self.ctx.log("error", "rugby",
                               f"Deep fetch failed for league {league_id}: {ex.detail}")
            raise

    async def _upsert_fixture(self, s, league_id, ev):
        fid = int(ev["idEvent"])
        fx = await s.get(RugbyFixture, fid)
        if fx is None:
            fx = RugbyFixture(id=fid)
            s.add(fx)
        fx.league_id = league_id
        fx.season = ev.get("strSeason") or ""
        fx.round = str(ev.get("intRound") or "")
        fx.date = _parse_date(ev.get("dateEvent"))
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
        async with self.ctx.session() as s:
            league_id = await self._league_for_sub(s, sub_id)
            if league_id is None:
                return None
            rows = (await s.execute(
                select(RugbyFixture).where(RugbyFixture.league_id == league_id)
            )).scalars().all()
            fixtures = [{"id": f.id, "home_name": f.home_name,
                         "away_name": f.away_name, "date": f.date,
                         "season": f.season, "round": f.round} for f in rows]
            text = item.file_name or item.caption or ""
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
    async def enrichment(self, channel_id) -> dict:
        """Match data for a channel's media, keyed by tg_msg_id (for Browse)."""
        out: dict = {}
        async with self.ctx.session() as s:
            rows = (await s.execute(
                select(MediaItem.tg_msg_id, RugbyMatch)
                .join(RugbyMatch, RugbyMatch.media_id == MediaItem.id)
                .where(MediaItem.channel_id == channel_id,
                       RugbyMatch.status.in_(("auto", "confirmed")))
            )).all()
            for tg_msg_id, m in rows:
                league = await s.get(RugbyLeague, m.league_id) if m.league_id else None
                fx = await s.get(RugbyFixture, m.fixture_id) if m.fixture_id else None
                home_badge = await self._team_badge(s, fx.home_team_id) if fx else None
                away_badge = await self._team_badge(s, fx.away_team_id) if fx else None
                out[tg_msg_id] = {
                    "league": league.name if league else None,
                    "league_badge": league.badge_url if league else None,
                    "season": m.season, "round": m.round,
                    "home": m.home_name, "away": m.away_name,
                    "home_badge": home_badge, "away_badge": away_badge,
                    "venue": fx.venue if fx else None,
                    "home_score": fx.home_score if fx else None,
                    "away_score": fx.away_score if fx else None,
                    "status": m.status,
                }
        return out

    async def _team_badge(self, s, team_id):
        if not team_id:
            return None
        t = await s.get(RugbyTeam, team_id)
        return t.badge_url if t else None

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
            return [_match_dict(m) for m in rows]

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


def _match_dict(m):
    return {"media_id": m.media_id, "fixture_id": m.fixture_id,
            "league_id": m.league_id, "season": m.season, "round": m.round,
            "home_name": m.home_name, "away_name": m.away_name,
            "confidence": m.confidence, "status": m.status}


def _current_season():
    # ponytail: rugby seasons span Sep-Jun; cheap heuristic without a clock arg.
    now = datetime.now(timezone.utc)
    start = now.year if now.month >= 7 else now.year - 1
    return f"{start}-{start + 1}"


def _recent_seasons():
    """Current + previous season as 'YYYY-YYYY' strings (covers a season rollover)."""
    now = datetime.now(timezone.utc)
    start = now.year if now.month >= 7 else now.year - 1
    return [f"{start}-{start + 1}", f"{start - 1}-{start}"]


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
