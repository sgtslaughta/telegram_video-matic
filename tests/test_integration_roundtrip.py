"""
Full round-trip integration test: Account encrypted → Channel → Topic → Subscription → MediaItem.
Status pending → queued (claim_pending). Verify atomicity and decrypt(encrypt(x)) == x.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.models import Base, MediaStatus
from app.db.repositories import (
    accounts, channels, topics, subscriptions, media, downloads, settings, events, tags
)
from app.crypto import encrypt, decrypt


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
async def test_crypto_roundtrip():
    """Verify encrypt(plaintext) then decrypt() returns original plaintext."""
    plaintext = "my_secret_api_hash_12345"
    ciphertext = encrypt(plaintext)
    decrypted = decrypt(ciphertext)

    assert decrypted == plaintext
    assert ciphertext != plaintext


@pytest.mark.asyncio
async def test_full_roundtrip_account_to_media_download(session):
    """
    Full workflow:
    1. Create Account with encrypted api_id/api_hash
    2. Create Channel
    3. Create Topic
    4. Create Subscription
    5. Create 5 MediaItems (all pending)
    6. Claim 3 pending → flips to queued (atomically)
    7. Start download jobs
    8. Verify media status transitions
    9. Add events and tags
    """
    # 1. Account
    account = await accounts.upsert(
        session=session,
        api_id="123456789",
        api_hash="abcdef123456hash",
        session_string="session_string_xyz",
    )

    assert account.id is not None
    # Verify encrypted
    assert decrypt(account.api_id_enc) == "123456789"
    assert decrypt(account.api_hash_enc) == "abcdef123456hash"
    assert decrypt(account.session_enc) == "session_string_xyz"

    # 2. Channel
    channel = await channels.upsert(
        session=session,
        tg_id=111222333,
        title="Test Channel",
        username="testchannel",
        is_forum=True,
        photo_b64=None,
        raw={"members": 1000},
    )

    assert channel.tg_id == 111222333

    # 3. Topic
    topic = await topics.upsert(
        session=session,
        channel_id=channel.id,
        tg_topic_id=1,
        title="Announcements",
        raw=None,
    )

    assert topic.tg_topic_id == 1
    assert topic.channel_id == channel.id

    # 4. Subscription
    sub = await subscriptions.create(
        session=session,
        channel_id=channel.id,
        topic_id=topic.id,
        storage_path="/media/channel",
        rename_template="{title} - {date}",
        enabled=True,
        filter_regex=".*video.*",
    )

    assert sub.enabled is True
    assert sub.storage_path == "/media/channel"

    # 5. Create 5 pending MediaItems
    items = []
    for i in range(1, 6):
        item = await media.upsert_from_tg(
            session=session,
            channel_id=channel.id,
            topic_id=topic.id,
            subscription_id=sub.id,
            tg_msg_id=1000 + i,
            caption=f"Video {i}",
            file_name=f"video_{i}.mp4",
            mime="video/mp4",
            size_bytes=1000000 * i,
            duration_sec=60 * i,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            raw=None,
        )
        assert item.status == MediaStatus.PENDING
        items.append(item)

    # 6. Claim 3 pending → flips to queued
    claimed = await media.claim_pending(session, limit=3)
    assert len(claimed) == 3
    for c in claimed:
        assert c.status == MediaStatus.QUEUED

    # Remaining 2 should still be pending
    claimed_again = await media.claim_pending(session, limit=10)
    assert len(claimed_again) == 2

    # 7. Start download jobs for claimed items
    for item in claimed:
        job = await downloads.start(session, item.id)
        assert job.media_id == item.id
        assert job.status == "queued"

    # 8. Finish first download
    first_job = await downloads.get(session, 1)
    assert first_job is not None
    await downloads.finish(session, first_job.id)

    # Verify media transitioned to downloaded
    media_item = await media.get(session, claimed[0].id)
    assert media_item.status == MediaStatus.DOWNLOADED
    assert media_item.downloaded_at is not None

    # 9. Add events and tags
    event = await events.add(
        session=session,
        level="success",
        kind="download",
        message="Video downloaded successfully",
        subscription_id=sub.id,
        media_id=claimed[0].id,
    )

    assert event.id is not None

    tag = await tags.add_tag(session, "favorite")
    await tags.tag_media(session, claimed[0].id, tag.id)

    # Verify subscription is still accessible
    subs = await subscriptions.list(session, channel.id, enabled_only=True)
    assert len(subs) == 1


@pytest.mark.asyncio
async def test_claim_pending_only_enabled_subscriptions(session):
    """claim_pending() only claims from enabled subscriptions."""
    channel = await channels.upsert(session, 999, "Ch", None, False, None, None)

    # Enabled sub
    sub_enabled = await subscriptions.create(session, channel.id, None, "/media", "{title}", enabled=True)

    # Disabled sub
    sub_disabled = await subscriptions.create(session, channel.id, None, "/media", "{title}", enabled=False)

    # Create media in both
    m1 = await media.upsert_from_tg(
        session, channel.id, None, sub_enabled.id, 101, "V1", None,
        None, None, None, datetime.now(timezone.utc), None, None,
    )

    m2 = await media.upsert_from_tg(
        session, channel.id, None, sub_disabled.id, 102, "V2", None,
        None, None, None, datetime.now(timezone.utc), None, None,
    )

    # Claim should only get m1
    claimed = await media.claim_pending(session, limit=10)

    assert len(claimed) == 1
    assert claimed[0].id == m1.id
