from dataclasses import dataclass
import pytest
from app.telegram.dtos import ChannelDTO, TopicDTO, MediaDTO


def test_channel_dto_construction():
    """ChannelDTO fields match spec 02 capabilities."""
    ch = ChannelDTO(
        tg_id=123456,
        title="Test Channel",
        username="testchannel",
        is_forum=False,
        photo_b64=None,
        raw={"peer_id": {"channel_id": 123456}}
    )
    assert ch.tg_id == 123456
    assert ch.title == "Test Channel"
    assert ch.username == "testchannel"
    assert ch.is_forum is False
    assert ch.photo_b64 is None


def test_topic_dto_construction():
    """TopicDTO fields for forum topic or synthetic General."""
    topic = TopicDTO(
        tg_topic_id=1,
        title="General",
        channel_tg_id=123456,
        raw={"topic_id": 1}
    )
    assert topic.tg_topic_id == 1
    assert topic.title == "General"
    assert topic.channel_tg_id == 123456


def test_media_dto_construction():
    """MediaDTO fields: file metadata, media info, reactions, comment count."""
    media = MediaDTO(
        tg_msg_id=999,
        channel_tg_id=123456,
        topic_tg_id=1,
        caption="Test video",
        file_name="video.mp4",
        mime="video/mp4",
        size_bytes=1024000,
        duration_sec=60,
        date_posted=None,
        thumb_b64=None,
        reactions={"👍": 5},
        comments_count=3,
        raw={"id": 999}
    )
    assert media.tg_msg_id == 999
    assert media.file_name == "video.mp4"
    assert media.size_bytes == 1024000
    assert media.reactions == {"👍": 5}
    assert media.comments_count == 3
