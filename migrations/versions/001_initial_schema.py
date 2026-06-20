"""Initial schema with all models.

Revision ID: 001
Revises:
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables."""
    op.create_table(
        "settings",
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.String(4096), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name="pk_settings"),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("api_id_enc", sa.String(1024), nullable=False),
        sa.Column("api_hash_enc", sa.String(1024), nullable=False),
        sa.Column("session_enc", sa.String(4096), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="disconnected"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
    )

    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("tg_id", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("is_forum", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("photo_b64", sa.String(8192), nullable=True),
        sa.Column("raw", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_channels"),
        sa.UniqueConstraint("tg_id", name="uq_channels_tg_id"),
    )

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("channel_id", sa.Integer, nullable=False),
        sa.Column("tg_topic_id", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("raw", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id", name="pk_topics"),
        sa.UniqueConstraint("channel_id", "tg_topic_id", name="uq_topics_channel_topic"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("channel_id", sa.Integer, nullable=False),
        sa.Column("topic_id", sa.Integer, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("mode", sa.String(32), nullable=False, server_default="immediate"),
        sa.Column("schedule_days", sa.JSON, nullable=True),
        sa.Column("filter_regex", sa.String(1024), nullable=True),
        sa.Column("filter_mode", sa.String(32), nullable=False, server_default="include"),
        sa.Column("min_size_mb", sa.Integer, nullable=True),
        sa.Column("max_size_mb", sa.Integer, nullable=True),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("rename_template", sa.String(1024), nullable=False),
        sa.Column("season_detection", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("retention_days", sa.Integer, nullable=True),
        sa.Column("retention_disk_pct", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
        sa.UniqueConstraint("channel_id", "topic_id", name="uq_subscriptions_channel_topic"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )

    op.create_table(
        "media_items",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("channel_id", sa.Integer, nullable=False),
        sa.Column("topic_id", sa.Integer, nullable=True),
        sa.Column("subscription_id", sa.Integer, nullable=True),
        sa.Column("tg_msg_id", sa.Integer, nullable=False),
        sa.Column("caption", sa.String(4096), nullable=True),
        sa.Column("file_name", sa.String(1024), nullable=True),
        sa.Column("mime", sa.String(255), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("duration_sec", sa.Integer, nullable=True),
        sa.Column("date_posted", sa.DateTime(timezone=True), nullable=False),
        sa.Column("thumb_b64", sa.String(8192), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reactions", sa.JSON, nullable=True),
        sa.Column("comments_count", sa.Integer, nullable=True),
        sa.Column("raw", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.PrimaryKeyConstraint("id", name="pk_media_items"),
        sa.UniqueConstraint("channel_id", "tg_msg_id", name="uq_media_items_channel_msg"),
    )

    op.create_table(
        "media_tags",
        sa.Column("media_id", sa.Integer, nullable=False),
        sa.Column("tag_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("media_id", "tag_id", name="pk_media_tags"),
    )

    op.create_table(
        "download_jobs",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("media_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("speed_bps", sa.Integer, nullable=True),
        sa.Column("eta_sec", sa.Integer, nullable=True),
        sa.Column("bytes_done", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bytes_total", sa.Integer, nullable=True),
        sa.Column("attempt", sa.Integer, nullable=False, server_default="1"),
        sa.Column("error", sa.String(1024), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"]),
        sa.PrimaryKeyConstraint("id", name="pk_download_jobs"),
    )

    op.create_table(
        "plugins",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_plugins"),
        sa.UniqueConstraint("name", name="uq_plugins_name"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("subscription_id", sa.Integer, nullable=True),
        sa.Column("media_id", sa.Integer, nullable=True),
        sa.Column("message", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.ForeignKeyConstraint(["media_id"], ["media_items.id"]),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("events")
    op.drop_table("plugins")
    op.drop_table("download_jobs")
    op.drop_table("media_tags")
    op.drop_table("media_items")
    op.drop_table("tags")
    op.drop_table("subscriptions")
    op.drop_table("topics")
    op.drop_table("channels")
    op.drop_table("accounts")
    op.drop_table("settings")
