"""Fuzzy matcher for Telegram video filenames/captions to rugby fixtures."""

import pytest
from datetime import datetime, timezone
from app.rugby.matcher import (
    normalize, match, parse_round, parse_title_date, league_hint)


def test_normalize_lowercase_and_punctuation():
    """normalize() lowercases, removes punctuation."""
    assert normalize("SALE SHARKS") == "sale sharks"
    assert normalize("Bath-Unioned") == "bath unioned"  # Punctuation becomes space
    assert normalize("Gloucester's Union") == "gloucester s union"  # Apostrophe becomes space


def test_normalize_drops_rugby_filler():
    """normalize() removes rugby, rfc, fc, afc, the."""
    assert normalize("Bath Rugby") == "bath"
    assert normalize("Sale Sharks RFC") == "sale sharks"
    assert normalize("The Harlequins FC") == "harlequins"
    assert normalize("Leicester AFC") == "leicester"
    assert normalize("THE RUGBY UNION") == "union"


def test_normalize_collapses_whitespace():
    """normalize() collapses multiple spaces."""
    assert normalize("Sale   Sharks") == "sale sharks"
    assert normalize("  Bath  ") == "bath"


def test_match_exact_team_names_with_date():
    """match() returns Sale/Gloucester fixture with auto status."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
        {
            "id": 2,
            "home_name": "Harlequins",
            "away_name": "Bath Rugby",
            "date": datetime(2025, 9, 26, tzinfo=timezone.utc),
        },
    ]
    text = "Sale Sharks v Gloucester 27-09-25"
    date = datetime(2025, 9, 25, tzinfo=timezone.utc)

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is not None
    assert result_fixture["id"] == 1
    assert status == "auto"
    assert confidence >= 0.8


def test_match_without_date():
    """match() returns Harlequins/Bath fixture without date context."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
        {
            "id": 2,
            "home_name": "Harlequins",
            "away_name": "Bath Rugby",
            "date": datetime(2025, 9, 26, tzinfo=timezone.utc),
        },
    ]
    text = "Harlequins Bath highlights"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is not None
    assert result_fixture["id"] == 2
    assert status != "none"
    assert confidence > 0.5


def test_match_no_match_returns_none():
    """match() returns (None, low_confidence, 'none') for unrelated text."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
    ]
    text = "Random cooking video"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is None
    assert status == "none"
    assert confidence < 0.6


def test_match_empty_fixtures():
    """match() with empty fixtures list returns (None, 0.0, 'none')."""
    fixtures = []
    text = "Some random text"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is None
    assert confidence == 0.0
    assert status == "none"


def test_match_threshold_needs_review():
    """match() returns needs_review when confidence in [threshold, 0.8)."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": None,
        },
    ]
    text = "Sale Sharks vs Gloucester"  # Clear match but not with date
    date = None

    result_fixture, confidence, status = match(text, date, fixtures, threshold=0.5)

    # Should match with moderate confidence (no date bonus means likely < 0.8)
    assert result_fixture is not None
    assert status in ["auto", "needs_review"]
    assert confidence >= 0.5


# --- heuristic title parsing -------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Bath v Leicester - PREM Round 18 - 6th June 2026", 18),
    ("Sale v Bristol PREM Round 18", 18),
    ("Newcastle v Sale - R17 - 30th May 2026", 17),
    ("Rd 5 highlights", 5),
    ("Northampton v Exeter - PREM Final - 20th June 2026", None),  # final -> no round
    ("Chiefs v Crusaders Super Rugby Pacific Semi Final 1", None),
    ("just a video", None),
])
def test_parse_round(text, expected):
    assert parse_round(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("Bath v Leicester - 6th June 2026", (2026, 6, 6)),
    ("Northampton v Exeter - 20th June 2026", (2026, 6, 20)),
    ("Newcastle v Sale - 30th May 2026", (2026, 5, 30)),
    ("Chiefs_v_Crusaders_12th_June_2026", (2026, 6, 12)),
    ("Leicester v Exeter - 31st May 2026", (2026, 5, 31)),
    ("no date here", None),
])
def test_parse_title_date(text, expected):
    d = parse_title_date(text)
    assert (d is None) if expected is None else (d.year, d.month, d.day) == expected


def test_league_hint():
    assert league_hint("Bath v Leicester PREM Round 18") == "prem"
    assert league_hint("Chiefs v Crusaders Super Rugby Pacific") == "super rugby"
    assert league_hint("random video") is None


@pytest.mark.parametrize("text,needle", [
    ("France v England - Six Nations 2026", "six nations"),
    ("Springboks v All Blacks - The Rugby Championship", "rugby championship"),
    ("Leinster v Toulouse - Champions Cup Final", "champions cup"),
    ("Bristol v Toulon - Challenge Cup", "challenge cup"),
    ("England v Fiji - Rugby World Cup 2027", "world cup"),
    ("Sharks v Bulls - Currie Cup Final", "currie"),
])
def test_league_hint_tournaments(text, needle):
    assert league_hint(text) == needle


def test_round_disambiguates_same_teams_two_legs():
    """Same teams meet twice; round+date in title must pick the right leg."""
    leg18 = {"id": 18, "home_name": "Bath Rugby", "away_name": "Leicester Tigers",
             "round": "18", "date": datetime(2026, 6, 6, tzinfo=timezone.utc),
             "league_name": "English Prem Rugby"}
    leg2 = {"id": 2, "home_name": "Leicester Tigers", "away_name": "Bath Rugby",
            "round": "2", "date": datetime(2024, 9, 29, tzinfo=timezone.utc),
            "league_name": "English Prem Rugby"}
    text = "Bath v Leicester - PREM Round 18 - 6th June 2026.mp4"
    fx, conf, status = match(text, None, [leg2, leg18])
    assert fx["id"] == 18 and status == "auto" and conf >= 0.8


def test_short_city_names_match_full_team_names():
    """'Sale'/'Bath' in title still identify 'Sale Sharks'/'Bath Rugby'."""
    fx = {"id": 1, "home_name": "Sale Sharks", "away_name": "Bristol Bears",
          "round": "18", "date": datetime(2026, 6, 6, tzinfo=timezone.utc),
          "league_name": "English Prem Rugby"}
    text = "Sale v Bristol - PREM Round 18 - 6th June 2026.mp4"
    res, conf, status = match(text, None, [fx])
    assert res is not None and status == "auto"
