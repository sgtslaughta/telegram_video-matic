import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.models import Base, Account, Channel, Topic, Subscription, MediaItem, MediaStatus
from app.db.repositories import (
    accounts, channels, topics, subscriptions, media, downloads, settings, events, tags, plugins
)


@pytest_asyncio.fixture
async def session():
    """Create in-memory test session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.mark.asyncio
async def test_accounts_upsert(session):
    """accounts.upsert() inserts or updates account with encrypted secrets."""
    # First upsert
    acc1 = await accounts.upsert(
        session=session,
        api_id="123456",
        api_hash="abc123hash",
        session_string=None,
    )

    assert acc1.id is not None
    assert acc1.api_id_enc != "123456"  # encrypted
    assert acc1.api_hash_enc != "abc123hash"  # encrypted

    # Second upsert should update
    acc2 = await accounts.upsert(
        session=session,
        api_id="999999",
        api_hash="xyz789",
        session_string="session_xyz",
    )

    assert acc2.id == acc1.id  # same account
    assert acc2.session_enc is not None


@pytest.mark.asyncio
async def test_channels_upsert(session):
    """channels.upsert() inserts or updates channel by tg_id."""
    ch1 = await channels.upsert(
        session=session,
        tg_id=111222333,
        title="Test Channel",
        username="testchan",
        is_forum=False,
        photo_b64=None,
        raw={"tg_data": "xyz"},
    )

    assert ch1.tg_id == 111222333
    assert ch1.title == "Test Channel"

    # Update
    ch2 = await channels.upsert(
        session=session,
        tg_id=111222333,
        title="Test Channel Updated",
        username="testchan",
        is_forum=True,
        photo_b64=None,
        raw=None,
    )

    assert ch2.id == ch1.id
    assert ch2.title == "Test Channel Updated"


@pytest.mark.asyncio
async def test_topics_upsert(session):
    """topics.upsert() ensures unique (channel_id, tg_topic_id)."""
    channel = await channels.upsert(session, 123, "Ch", None, False, None, None)

    topic1 = await topics.upsert(
        session=session,
        channel_id=channel.id,
        tg_topic_id=1,
        title="Topic 1",
        raw=None,
    )

    assert topic1.tg_topic_id == 1

    # Same (channel, tg_topic_id) updates
    topic2 = await topics.upsert(
        session=session,
        channel_id=channel.id,
        tg_topic_id=1,
        title="Topic 1 Updated",
        raw=None,
    )

    assert topic2.id == topic1.id
    assert topic2.title == "Topic 1 Updated"


@pytest.mark.asyncio
async def test_subscriptions_crud(session):
    """subscriptions.create/list/update/delete."""
    channel = await channels.upsert(session, 999, "Ch", None, False, None, None)

    # Create
    sub1 = await subscriptions.create(
        session=session,
        channel_id=channel.id,
        topic_id=None,
        storage_path="/media",
        rename_template="{title}",
        enabled=True,
    )

    assert sub1.id is not None
    assert sub1.enabled is True

    # List
    subs = await subscriptions.list(session, channel.id, enabled_only=True)
    assert len(subs) == 1

    # Update
    await subscriptions.update(session, sub1.id, enabled=False)
    subs = await subscriptions.list(session, channel.id, enabled_only=True)
    assert len(subs) == 0

    # Delete
    await subscriptions.delete(session, sub1.id)
    subs = await subscriptions.list(session, channel.id, enabled_only=False)
    assert len(subs) == 0


@pytest.mark.asyncio
async def test_media_claim_pending_atomicity(session):
    """media.claim_pending(limit) atomically flips pending→queued."""
    # Setup: channel, subscription, media items
    channel = await channels.upsert(session, 888, "Ch", None, False, None, None)
    sub = await subscriptions.create(session, channel.id, None, "/media", "{title}", True)

    # Create 3 pending media items
    m1 = await media.upsert_from_tg(
        session=session,
        channel_id=channel.id,
        topic_id=None,
        subscription_id=sub.id,
        tg_msg_id=1,
        caption="Video 1",
        file_name="v1.mp4",
        mime="video/mp4",
        size_bytes=1000000,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        thumb_b64=None,
        raw=None,
    )

    m2 = await media.upsert_from_tg(
        session=session,
        channel_id=channel.id,
        topic_id=None,
        subscription_id=sub.id,
        tg_msg_id=2,
        caption="Video 2",
        file_name="v2.mp4",
        mime="video/mp4",
        size_bytes=2000000,
        duration_sec=120,
        date_posted=datetime.now(timezone.utc),
        thumb_b64=None,
        raw=None,
    )

    # Claim 1 pending
    claimed = await media.claim_pending(session, limit=1)

    assert len(claimed) == 1
    assert claimed[0].status == MediaStatus.QUEUED

    # Claim 1 more
    claimed2 = await media.claim_pending(session, limit=1)
    assert len(claimed2) == 1

    # Test: pending items in disabled subscriptions are NOT claimed
    sub_disabled = await subscriptions.create(session, channel.id, None, "/media", "{title}", enabled=False)
    m3 = await media.upsert_from_tg(
        session=session,
        channel_id=channel.id,
        topic_id=None,
        subscription_id=sub_disabled.id,
        tg_msg_id=3,
        caption="Video 3",
        file_name="v3.mp4",
        mime="video/mp4",
        size_bytes=3000000,
        duration_sec=180,
        date_posted=datetime.now(timezone.utc),
        thumb_b64=None,
        raw=None,
    )

    claimed3 = await media.claim_pending(session, limit=10)
    assert len(claimed3) == 0  # Should not claim from disabled subscription

    # Verify the item is still PENDING
    m3_refreshed = await media.get(session, m3.id)
    assert m3_refreshed.status == MediaStatus.PENDING

    # Test: already-QUEUED items are not re-claimed
    claimed4 = await media.claim_pending(session, limit=10)
    assert len(claimed4) == 0  # No pending items left (all queued or in disabled sub)


@pytest.mark.asyncio
async def test_downloads_lifecycle(session):
    """downloads.start/update_progress/finish."""
    channel = await channels.upsert(session, 777, "Ch", None, False, None, None)
    sub = await subscriptions.create(session, channel.id, None, "/media", "{title}", True)

    item = await media.upsert_from_tg(
        session, channel.id, None, sub.id, 100, "Test", "test.mp4",
        "video/mp4", 5000000, 300, datetime.now(timezone.utc), None, None,
    )

    # Start download
    job = await downloads.start(session, item.id)
    assert job.status == "queued"

    # Update progress
    await downloads.update_progress(session, job.id, bytes_done=2500000, eta_sec=150, speed_bps=1000000)

    # Finish
    await downloads.finish(session, job.id)


@pytest.mark.asyncio
async def test_settings_get_set(session):
    """settings.get/set."""
    await settings.set(session, "test_key", '{"value": 42}')
    val = await settings.get(session, "test_key")
    assert '42' in val


@pytest.mark.asyncio
async def test_tags_workflow(session):
    """tags.add_tag/tag_media/list_tags."""
    tag = await tags.add_tag(session, "action")
    assert tag.name == "action"

    channel = await channels.upsert(session, 666, "Ch", None, False, None, None)
    sub = await subscriptions.create(session, channel.id, None, "/media", "{title}", True)
    item = await media.upsert_from_tg(
        session, channel.id, None, sub.id, 200, "Title", None,
        None, None, None, datetime.now(timezone.utc), None, None,
    )

    await tags.tag_media(session, item.id, tag.id)
    all_tags = await tags.list_tags(session)
    assert len(all_tags) >= 1
