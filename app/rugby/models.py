"""Plugin-owned SQLAlchemy models (on the shared Base).

These tables are created by the host's create_models() at enable, NOT by a core
migration. Core never references them — deleting the plugin leaves core intact.
rugby_match / rugby_subscription reference core tables (one-directional), which
is fine: the dependency points plugin -> core, never core -> plugin.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import UTCDateTime, Base, TimestampMixin


class RugbyLeague(Base, TimestampMixin):
    __tablename__ = "rugby_leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # thesportsdb id
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sport: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # union|league
    country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # Featured/Cup/...
    badge_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tracked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_deep_fetch_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime(), nullable=True)


class RugbyTeam(Base, TimestampMixin):
    __tablename__ = "rugby_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # thesportsdb id
    league_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rugby_leagues.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    alt_names: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    stadium: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    badge_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    badge_local: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    logo_local: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)


class RugbyFixture(Base, TimestampMixin):
    __tablename__ = "rugby_fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # thesportsdb event id
    league_id: Mapped[int] = mapped_column(ForeignKey("rugby_leagues.id"), nullable=False)
    season: Mapped[str] = mapped_column(String(16), nullable=False)
    round: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime(), nullable=True)
    home_team_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_team_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    away_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class RugbyMatch(Base, TimestampMixin):
    """One Telegram media item resolved to a rugby fixture (+ review state)."""
    __tablename__ = "rugby_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("media_items.id"), unique=True, nullable=False)
    fixture_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rugby_fixtures.id"), nullable=True)
    league_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rugby_leagues.id"), nullable=True)
    season: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    round: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    home_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    away_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # auto | needs_review | confirmed | rejected
    status: Mapped[str] = mapped_column(String(32), default="needs_review", nullable=False)


class RugbySubscription(Base, TimestampMixin):
    """Links a core Subscription to the rugby league(s) it carries (the
    deep-fetch trigger and a match hint). One topic can carry several
    competitions, e.g. Champions Cup + Challenge Cup."""
    __tablename__ = "rugby_subscriptions"

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id"), primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("rugby_leagues.id"), primary_key=True)


def migrate_subscription_links(conn) -> None:
    """Pre-1.10 the table keyed on subscription_id alone (one league per
    subscription). Rebuild it with a (subscription_id, league_id) key, keeping
    rows. SQLite can't alter a primary key in place. Idempotent."""
    from sqlalchemy import text
    cols = conn.execute(text("PRAGMA table_info(rugby_subscriptions)")).all()
    if not cols:
        return  # fresh install: create_all builds the new shape
    pk = [c[1] for c in cols if c[5]]
    if pk != ["subscription_id"]:
        return
    conn.execute(text("ALTER TABLE rugby_subscriptions RENAME TO rugby_subscriptions_old"))
    conn.execute(text(
        "CREATE TABLE rugby_subscriptions (subscription_id INTEGER NOT NULL REFERENCES subscriptions(id),"
        " league_id INTEGER NOT NULL REFERENCES rugby_leagues(id), created_at DATETIME, updated_at DATETIME,"
        " PRIMARY KEY (subscription_id, league_id))"))
    conn.execute(text(
        "INSERT INTO rugby_subscriptions (subscription_id, league_id, created_at, updated_at)"
        " SELECT subscription_id, league_id, created_at, updated_at FROM rugby_subscriptions_old"))
    conn.execute(text("DROP TABLE rugby_subscriptions_old"))


class RugbyWantedState(Base, TimestampMixin):
    """Track search state and dismissal for a fixture in wanted list."""
    __tablename__ = "rugby_wanted_state"

    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("rugby_fixtures.id"), primary_key=True)
    last_searched_at: Mapped[Optional[datetime]] = mapped_column(
        UTCDateTime(), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gave_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


ALL_MODELS = [
    RugbyLeague, RugbyTeam, RugbyFixture, RugbyMatch, RugbySubscription,
    RugbyWantedState,
]
