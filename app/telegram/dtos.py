from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class ChannelDTO:
    """Telegram channel (Channel type only, not User/Bot)."""
    tg_id: int
    title: str
    username: Optional[str]
    is_forum: bool
    photo_b64: Optional[str]
    raw: Dict[str, Any]


@dataclass
class TopicDTO:
    """Forum topic within a channel; synthetic General for non-forum."""
    tg_topic_id: int
    title: str
    channel_tg_id: int
    raw: Dict[str, Any]


@dataclass
class MediaDTO:
    """Telegram media message (video/document)."""
    tg_msg_id: int
    channel_tg_id: int
    topic_tg_id: Optional[int]
    caption: Optional[str]
    file_name: Optional[str]
    mime: Optional[str]
    size_bytes: Optional[int]
    duration_sec: Optional[int]
    date_posted: Optional[datetime]
    thumb_b64: Optional[str]
    reactions: Optional[Dict[str, int]]
    comments_count: Optional[int]
    raw: Dict[str, Any]
