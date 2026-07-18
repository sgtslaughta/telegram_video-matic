"""Heuristic matcher: Telegram video title/caption -> rugby fixture.

A filename like "Bath v Leicester - PREM Round 18 - 6th June 2026.mp4" carries
four independent signals. The same two teams meet twice a season, so team names
alone are ambiguous; round and date are what pick the right leg.

Scoring (per fixture, both teams must be present to be a candidate):
  age-grade/gender/format disagree -> 0.0 (veto: U20 England is not England)
  base 0.6  + up to 0.2 team-token coverage  (both teams must be present)
  round in title == fixture round  -> +0.25   (mismatch -> -0.45)
  date  in title within 2d         -> +0.30   (>14d -> -0.40)
    else upload date within 3d     -> +0.15
  league hint in title matches     -> +0.05   (names another league -> -0.35)
Clamped to [0,1]. auto >= 0.8, needs_review >= 0.6, else none.
Team names alone cap at 0.79 (needs_review): the same two sides meet in several
competitions a year, so round, date or league must corroborate before auto-filing.
"""

import re
from datetime import datetime, timezone

# Words dropped during team-name normalization (generic rugby noise).
FILLER_WORDS = {"rugby", "rfc", "fc", "afc", "the", "club"}

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

# League/tournament hint tokens -> substring that must appear in the fixture's
# league name. Tournaments (Six Nations, World Cup, Champions Cup, ...) are
# modelled as leagues in thesportsdb, so they map the same way. Order matters:
# longer/more-specific phrases first (first hit wins in league_hint()).
_LEAGUE_HINTS = {
    # club leagues
    "premiership": "prem", "gallagher": "prem", "prem": "prem",
    "united rugby": "united rugby", "urc": "united rugby",
    "top 14": "top 14", "top14": "top 14",
    "super rugby": "super rugby", "super": "super rugby",
    "currie cup": "currie", "currie": "currie",
    # cross-league cups
    "champions cup": "champions cup", "challenge cup": "challenge cup",
    # international tournaments
    "six nations": "six nations",
    "rugby championship": "rugby championship",
    "trc": "rugby championship",            # The Rugby Championship
    "rugby europe": "rugby europe",
    "pacific nations": "pacific nations",
    "nations championship": "nations championship",
    # Junior World Championship first: it contains "world cup" as a substring and
    # would otherwise resolve to the senior Rugby World Cup. thesportsdb has no
    # JWC league, so this needle matches nothing on purpose — a JWC video ends up
    # unmatched (reviewable) rather than filed under a senior tournament.
    "junior world": "junior world", "jwc": "junior world", "jrwc": "junior world",
    "world cup": "world cup",
    "npc": "national provincial",           # NZ National Provincial Championship
}

# Age-grade / gender / format qualifiers. An U20 or women's fixture reuses the
# senior team names ("England v France"), so team matching alone happily files a
# Junior World Championship game under a senior tournament. The qualifiers of the
# title and of the fixture must agree exactly — a mismatch is a veto, not a
# penalty, because no amount of date/round agreement makes it the same game.
_GRADES = {
    "u20": r"u-?\s?20s?\b|under-?\s?20s?\b|junior world|\bjwc\b|\bjrwc\b",
    "u19": r"u-?\s?19s?\b|under-?\s?19s?\b",
    "u18": r"u-?\s?18s?\b|under-?\s?18s?\b",
    "women": r"\bwomen\b|\bwomens\b|\bwomen's\b|\bladies\b|\bwxv\b",
    "sevens": r"\b7s\b|\bsevens\b",
}


def grades(text: str) -> frozenset[str]:
    """Age-grade/gender/format tags present in a title or league name."""
    low = (text or "").lower()
    return frozenset(g for g, pat in _GRADES.items() if re.search(pat, low))


def normalize(name: str) -> str:
    """Lowercase, strip punctuation, drop filler words, collapse whitespace."""
    s = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    return " ".join(t for t in s.split() if t not in FILLER_WORDS)


def team_tokens(name: str) -> list[str]:
    """Significant (>=3 char) identifying tokens of a team name."""
    return [t for t in normalize(name).split() if len(t) >= 3]


def team_coverage(name: str, text_norm: str) -> tuple[bool, float]:
    """Is the team identifiable in the text, and what token fraction matched.

    A team is 'present' if any one of its identifying tokens appears (a title
    often uses just the city — "Bath" for "Bath Rugby", "Leicester" for
    "Leicester Tigers"). Coverage refines ties.
    """
    toks = team_tokens(name)
    if not toks:
        return (False, 0.0)
    found = sum(1 for t in toks if t in text_norm)
    return (found > 0, found / len(toks))


def parse_round(text: str) -> int | None:
    """Pull a numeric round from a title. None for finals/unparseable.

    Finals/semis carry no reliable numeric round here, so they return None and
    are matched on date instead.
    """
    low = text.lower()
    if re.search(r"\b(semi|quarter|final|playoff|play-off|grand final)\b", low):
        return None
    m = (re.search(r"\bround\s*(\d{1,2})\b", low)
         or re.search(r"\brd\s*(\d{1,2})\b", low)
         or re.search(r"\br(\d{1,2})\b", low))
    return int(m.group(1)) if m else None


def parse_title_date(text: str) -> datetime | None:
    """Parse a human date embedded in a title.

    Handles "6th June 2026", "20th_June_2026", "31st May 2026" (separators may
    be spaces or underscores).
    """
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?[\s_]+([a-zA-Z]{3,})[\s_]+(\d{4})", text)
    if not m:
        return None
    day, mon, year = int(m.group(1)), m.group(2)[:3].lower(), int(m.group(3))
    month = _MONTHS.get(mon)
    if not month:
        return None
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def league_hint(text: str) -> str | None:
    """Substring a fixture's league name should contain, inferred from title."""
    low = text.lower()
    for token, needle in _LEAGUE_HINTS.items():
        if token in low:
            return needle
    return None


def _as_utc(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def score_fixture(text: str, upload_date: datetime | None, fixture: dict,
                  context: str = "") -> float:
    """Multi-factor score for one fixture. 0.0 means 'not a candidate'.

    `context` is the source channel/topic name. Uploaders name topics after the
    competition ("JWC", "URC"), which is often the only place the grade or league
    appears at all — titles routinely say just "England v France". It feeds the
    grade veto and the league hint only; round and date still come from the title,
    which is the only text describing this one game.
    """
    league_name = fixture.get("league_name") or ""

    # Veto: age-grade/gender/format must agree. Checked before team names because
    # the team names are exactly what collides across grades.
    if grades(f"{text} {context}") != grades(
            f"{league_name} {fixture.get('home_name') or ''} "
            f"{fixture.get('away_name') or ''}"):
        return 0.0

    tnorm = normalize(text)
    home_present, home_cov = team_coverage(fixture["home_name"] or "", tnorm)
    away_present, away_cov = team_coverage(fixture["away_name"] or "", tnorm)
    if not (home_present and away_present):
        return 0.0

    score = 0.6 + 0.2 * ((home_cov + away_cov) / 2.0)
    # Teams alone are never enough to auto-file: the same two sides meet in
    # several competitions a year. Something else has to agree.
    corroborated = False

    # Round: decisive between the two same-team legs of a season.
    title_round = parse_round(text)
    fx_round = _to_int(fixture.get("round"))
    if title_round is not None and fx_round is not None:
        if title_round == fx_round:
            score += 0.25
            corroborated = True
        else:
            score -= 0.45

    # Date: title date is the strongest disambiguator; upload date is a backup.
    fx_date = fixture.get("date")
    title_date = parse_title_date(text)
    if title_date is not None and fx_date is not None:
        dd = abs((_as_utc(fx_date).date() - title_date.date()).days)
        score += 0.30 if dd <= 2 else (0.10 if dd <= 7 else (-0.40 if dd > 14 else 0.0))
        corroborated = corroborated or dd <= 7
    elif upload_date is not None and fx_date is not None:
        dd = abs((_as_utc(fx_date).date() - _as_utc(upload_date).date()).days)
        score += 0.15 if dd <= 3 else (-0.20 if dd > 14 else 0.0)
        corroborated = corroborated or dd <= 3

    # League hint. The title naming a different competition than the fixture's
    # league is strong evidence against it, so a miss costs more than a hit pays.
    needle = league_hint(text) or league_hint(context)
    if needle and league_name:
        if needle in league_name.lower():
            score += 0.05
            corroborated = True
        else:
            score -= 0.35

    if not corroborated:
        score = min(score, 0.79)  # cap below the auto threshold
    return max(0.0, min(1.0, score))


def match(
    text: str,
    date: datetime | None,
    fixtures: list[dict],
    threshold: float = 0.6,
    context: str = "",
) -> tuple[dict | None, float, str]:
    """Pick the best-scoring fixture for a title.

    Returns (fixture|None, confidence, status). status in
    {"auto" (>=0.8), "needs_review" (>=threshold), "none"}.
    """
    best_fixture, best = None, 0.0
    for fixture in fixtures:
        s = score_fixture(text, date, fixture, context)
        if s > best:
            best, best_fixture = s, fixture
    if best >= threshold:
        return (best_fixture, best, "auto" if best >= 0.8 else "needs_review")
    return (None, best, "none")


def _to_int(v) -> int | None:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _demo() -> None:
    """Self-check: the right leg wins on round+date despite identical teams."""
    from datetime import datetime as _dt
    leg18 = {"id": 1, "home_name": "Bath Rugby", "away_name": "Leicester Tigers",
             "round": "18", "date": _dt(2026, 6, 6), "league_name": "English Prem Rugby"}
    leg2 = {"id": 2, "home_name": "Leicester Tigers", "away_name": "Bath Rugby",
            "round": "2", "date": _dt(2024, 9, 29), "league_name": "English Prem Rugby"}
    title = "Bath v Leicester - PREM Round 18 - 6th June 2026.mp4"
    fx, conf, status = match(title, None, [leg18, leg2])
    assert fx["id"] == 1, fx
    assert status == "auto" and conf >= 0.8, (conf, status)
    # No date/round, just teams -> a candidate, but never auto-filed.
    fx2, c2, st2 = match("Sale v Bristol.mp4", None,
                         [{"id": 9, "home_name": "Sale Sharks",
                           "away_name": "Bristol Bears", "round": "5",
                           "date": None, "league_name": "x"}])
    assert fx2 is not None and st2 == "needs_review", (c2, st2)
    # An U20 game must not file under the senior tournament sharing its teams.
    senior = {"id": 3, "home_name": "England", "away_name": "France",
              "round": "3", "date": _dt(2026, 7, 4),
              "league_name": "Rugby World Cup"}
    assert match("England U20 v France U20 - JWC - 4th July 2026.mp4",
                 None, [senior])[2] == "none"
    u20 = dict(senior, id=4, league_name="World Rugby U20 Championship")
    assert match("England U20 v France U20 - 4th July 2026.mp4",
                 None, [u20])[0]["id"] == 4
    # Non-rugby title matches nothing.
    assert match("random cooking video.mp4", None, [leg18])[2] == "none"
    print("matcher demo ok")


if __name__ == "__main__":
    _demo()
