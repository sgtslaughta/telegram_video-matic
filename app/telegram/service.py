import asyncio
import base64
import inspect
import pathlib
from collections import OrderedDict
from typing import Callable, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.messages import GetForumTopicsRequest

from app.db.models import Account, AccountStatus
from app.crypto import decrypt, encrypt
from app.telegram.dtos import ChannelDTO, TopicDTO, MediaDTO
from app.telegram.fast_telethon import download_file


class TelegramService:
    """Singleton Telethon client wrapper. Manages login, session persistence, read-only browse/download."""

    def __init__(
        self,
        account_repo,
        client_factory: Callable = TelegramClient,
        max_concurrent_downloads: int = 5,
        event_sink: Optional[Callable] = None
    ):
        """
        Initialize service.

        Args:
            account_repo: AccountRepository for DB access.
            client_factory: Factory to create TelegramClient (injectable for testing).
            max_concurrent_downloads: Semaphore bound for downloads.
            event_sink: Optional async callable(level, kind, message) for emitting events on errors.
        """
        self.account_repo = account_repo
        self.client_factory = client_factory
        self.client: Optional[TelegramClient] = None
        self.account: Optional[Account] = None
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self._login_lock = asyncio.Lock()
        self._phone_code_hash: Optional[str] = None
        self.event_sink = event_sink
        # Browse thumbnails are otherwise re-fetched from Telegram (2 RPCs each)
        # on every request. Bounded in-memory LRU; small (~KB each), lost on
        # restart. ponytail: in-memory, swap for a table if cross-restart matters.
        self._thumb_cache: "OrderedDict[tuple[int, int], str]" = OrderedDict()

    async def load_account(self) -> None:
        """Load Account from DB; build client whenever API credentials exist.

        Builds with the saved session if present, else an empty session so a
        configured-but-not-yet-logged-in account survives restarts (login can
        proceed without re-entering credentials).
        """
        self.account = await self.account_repo.get()
        if not self.account or not self.account.api_id_enc:
            return
        api_id = int(decrypt(self.account.api_id_enc))
        api_hash = decrypt(self.account.api_hash_enc)
        session_str = decrypt(self.account.session_enc) if self.account.session_enc else None
        try:
            session = StringSession(session_str) if session_str else StringSession()
        except ValueError:
            # Invalid session string (e.g., test mode) → empty session
            session = StringSession()
        self.client = self.client_factory(session, api_id, api_hash)

        # A half-completed login (awaiting code/password) cannot resume after a
        # restart — the in-memory phone_code_hash is gone. Reset to disconnected
        # so the UI starts the login over instead of stranding on the code step.
        if not self.account.session_enc and str(self.account.status) in (
            AccountStatus.AWAITING_CODE,
            AccountStatus.AWAITING_PASSWORD,
        ):
            await self.account_repo.update_status(self.account.id, AccountStatus.DISCONNECTED)
            self.account.status = AccountStatus.DISCONNECTED

    async def connect(self) -> None:
        """Connect to Telegram; update status to connected if authorized."""
        if not self.client:
            return
        await self.client.connect()
        if await self.client.is_user_authorized():
            await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)

    async def disconnect(self) -> None:
        """Persist encrypted session; disconnect and mark disconnected."""
        if not self.client or not self.account:
            return

        # Persist session
        session_str = self.client.session.save()
        await self.account_repo.update_session(self.account.id, encrypt(session_str))

        # Disconnect
        await self.client.disconnect()

        # Update status
        await self.account_repo.update_status(self.account.id, AccountStatus.DISCONNECTED)

    async def set_credentials(self, api_id: str, api_hash: str) -> None:
        """Store Telegram API credentials and build a fresh client for login."""
        async with self._login_lock:
            await self.account_repo.upsert_credentials(api_id, api_hash)
            self.account = await self.account_repo.get()
            self.client = self.client_factory(StringSession(None), int(api_id), api_hash)

    async def start_login(self, phone: str) -> None:
        """Start login: send code request."""
        async with self._login_lock:
            if not self.client:
                raise RuntimeError("Client not initialized")

            # Telethon requires an active connection before sending requests
            if not self.client.is_connected():
                await self.client.connect()

            sent_code = await self.client.send_code_request(phone)
            self._phone_code_hash = sent_code.phone_code_hash

            await self.account_repo.update_phone(self.account.id, phone)
            await self.account_repo.update_status(self.account.id, AccountStatus.AWAITING_CODE)

    async def submit_code(self, code: str) -> None:
        """Submit code; if 2FA required, status → awaiting_password; else → connected."""
        async with self._login_lock:
            if not self.client or not self.account or not self._phone_code_hash:
                raise RuntimeError("Login not started or client missing")

            try:
                await self.client.sign_in(
                    self.account.phone,
                    code,
                    phone_code_hash=self._phone_code_hash
                )
                # Success: persist session and mark connected
                session_str = self.client.session.save()
                await self.account_repo.update_session(self.account.id, encrypt(session_str))
                await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)
            except SessionPasswordNeededError:
                # 2FA required
                await self.account_repo.update_status(self.account.id, AccountStatus.AWAITING_PASSWORD)

    async def submit_password(self, password: str) -> None:
        """Submit 2FA password; on success, persist session and mark connected."""
        async with self._login_lock:
            if not self.client or not self.account:
                raise RuntimeError("Client not initialized or account missing")

            await self.client.sign_in(password=password)
            session_str = self.client.session.save()
            await self.account_repo.update_session(self.account.id, encrypt(session_str))
            await self.account_repo.update_status(self.account.id, AccountStatus.CONNECTED)

    async def logout(self) -> None:
        """Logout: call client.log_out(), clear session, mark disconnected."""
        async with self._login_lock:
            if not self.client or not self.account:
                return

            await self.client.log_out()
            await self.account_repo.update_session(self.account.id, None)
            await self.account_repo.update_status(self.account.id, AccountStatus.DISCONNECTED)

    # ========================================================================
    # Task 5: Read-only fetch methods
    # ========================================================================

    async def _channel_input(self, tg_id: int):
        """Resolve a channel's input entity. A bare int is treated by Telethon as
        a user; wrap in PeerChannel so it resolves as a channel (access hash comes
        from the session cache populated by get_dialogs)."""
        from telethon.tl.types import PeerChannel
        return await self.client.get_input_entity(PeerChannel(tg_id))

    async def list_channels(self, limit: int = 200) -> list[ChannelDTO]:
        """List all subscribed channels (Channel type only)."""
        if not self.client:
            return []

        try:
            dialogs = await self.client.get_dialogs(limit=limit)
        except FloodWaitError as e:
            # Log event if sink available; sleep and return empty
            if self.event_sink:
                await self.event_sink(
                    "warning",
                    "sync",
                    f"Rate limit hit while fetching channels; waiting {e.seconds}s"
                )
            await asyncio.sleep(e.seconds)
            return []

        channels = []

        for dialog in dialogs:
            from telethon.tl.types import Channel
            if isinstance(dialog.entity, Channel):
                channel = ChannelDTO(
                    tg_id=dialog.entity.id,
                    title=dialog.entity.title,
                    username=dialog.entity.username,
                    is_forum=getattr(dialog.entity, "forum", False),
                    photo_b64=None,
                    raw={"entity": dialog.entity}
                )
                channels.append(channel)

        return channels

    async def list_topics(self, channel: ChannelDTO, limit: int = 100) -> list[TopicDTO]:
        """List forum topics in a channel; synthetic General for non-forum."""
        if not channel.is_forum:
            # Non-forum: return synthetic General topic
            return [
                TopicDTO(
                    tg_topic_id=1,
                    title="General",
                    channel_tg_id=channel.tg_id,
                    raw={}
                )
            ]

        if not self.client:
            return []

        # Forum channel: fetch topics
        result = await self.client(GetForumTopicsRequest(
            peer=await self._channel_input(channel.tg_id),
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=limit
        ))

        topics = []
        for topic in result.topics:
            topics.append(TopicDTO(
                tg_topic_id=topic.id,
                title=topic.title,
                channel_tg_id=channel.tg_id,
                raw={"topic": topic}
            ))

        return topics

    async def browse_media(
        self, channel: ChannelDTO, topic: Optional[TopicDTO] = None,
        limit: int = 50, offset_id: int = 0,
    ):
        """Lightweight live media listing for browsing, paginated by VIDEO count.

        Scans messages older than `offset_id` until `limit` videos are collected
        (or a raw-scan safety cap is hit), so every page returns a consistent
        number of videos regardless of how much chat is interleaved.
        Returns (items, next_offset_id, has_more); next_offset_id is the smallest
        scanned id — pass it back to load older."""
        if not self.client:
            return [], None, False
        from telethon.tl.types import (
            MessageMediaDocument, DocumentAttributeFilename, DocumentAttributeVideo,
        )
        entity = await self._channel_input(channel.tg_id)
        extra = {}
        if topic and channel.is_forum:
            extra["reply_to"] = topic.tg_topic_id
        items = []
        scanned = 0
        last_id = None
        # Cap raw scanning so a video-sparse channel can't iterate forever.
        max_scan = max(limit * 20, 200)
        async for message in self.client.iter_messages(entity, offset_id=offset_id, **extra):
            scanned += 1
            last_id = message.id  # newest-first, so this ends at the smallest id
            if message.media and isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if doc.mime_type and doc.mime_type.startswith(("video/", "application/octet-stream")):
                    file_name = None
                    duration_sec = None
                    for attr in (doc.attributes or []):
                        if isinstance(attr, DocumentAttributeFilename):
                            file_name = attr.file_name
                        elif isinstance(attr, DocumentAttributeVideo):
                            duration_sec = attr.duration
                    items.append({
                        "tg_msg_id": message.id,
                        "caption": message.message or None,
                        "file_name": file_name,
                        "mime": doc.mime_type,
                        "size_bytes": doc.size,
                        "duration_sec": int(duration_sec) if duration_sec else None,
                        "date_posted": message.date,
                    })
            if len(items) >= limit or scanned >= max_scan:
                # Stopped early -> more may remain beyond last_id.
                return items, last_id, True
        # Iterator exhausted -> reached the end of the channel/topic.
        return items, last_id, False

    _THUMB_CACHE_MAX = 1024

    async def thumb_b64_for(self, channel_tg_id: int, msg_id: int) -> Optional[str]:
        """Resolve a message by id and return its thumbnail as base64, or None.
        Cached in a bounded LRU so repeat/Browse renders don't re-hit Telegram."""
        if not self.client:
            return None
        key = (channel_tg_id, msg_id)
        cached = self._thumb_cache.get(key)
        if cached is not None:
            self._thumb_cache.move_to_end(key)
            return cached
        try:
            entity = await self._channel_input(channel_tg_id)
            msg = await self.client.get_messages(entity, ids=msg_id)
            if not msg:
                return None
            b64 = await self.fetch_thumb(msg)
        except Exception:
            return None
        if b64:
            self._thumb_cache[key] = b64
            self._thumb_cache.move_to_end(key)
            if len(self._thumb_cache) > self._THUMB_CACHE_MAX:
                self._thumb_cache.popitem(last=False)
        return b64

    async def iter_media(
        self,
        channel: ChannelDTO,
        topic: Optional[TopicDTO] = None,
        since_msg_id: Optional[int] = None
    ):
        """Iterate media messages (video/document) in channel/topic, optionally from since_msg_id."""
        if not self.client:
            return

        try:
            entity = await self._channel_input(channel.tg_id)
            # For forum channels, scope messages to the chosen topic.
            extra = {}
            if topic and channel.is_forum:
                extra["reply_to"] = topic.tg_topic_id
            async for message in self.client.iter_messages(
                entity,
                min_id=since_msg_id or 0,
                reverse=False,
                **extra
            ):
                # Filter for video/document media
                if not message.media:
                    continue

                from telethon.tl.types import MessageMediaDocument
                if not isinstance(message.media, MessageMediaDocument):
                    continue

                doc = message.media.document
                if not doc.mime_type or not doc.mime_type.startswith(("video/", "application/octet-stream")):
                    continue

                # Extract file name from attributes
                file_name = None
                duration_sec = None
                if doc.attributes:
                    from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            file_name = attr.file_name
                        elif isinstance(attr, DocumentAttributeVideo):
                            duration_sec = attr.duration

                # Fetch reactions and comment count
                reactions_dict = await self.fetch_reactions(message)
                comments_count = await self.fetch_comment_count(message)

                media = MediaDTO(
                    tg_msg_id=message.id,
                    channel_tg_id=channel.tg_id,
                    topic_tg_id=topic.tg_topic_id if topic else None,
                    caption=message.text or message.message,
                    file_name=file_name,
                    mime=doc.mime_type,
                    size_bytes=doc.size,
                    duration_sec=duration_sec,
                    date_posted=message.date,
                    thumb_b64=None,
                    reactions=reactions_dict,
                    comments_count=comments_count,
                    raw={}
                )

                yield media
        except FloodWaitError as e:
            # Log event if sink available; sleep and return
            if self.event_sink:
                await self.event_sink(
                    "warning",
                    "sync",
                    f"Rate limit hit while fetching media; waiting {e.seconds}s"
                )
            await asyncio.sleep(e.seconds)
            return

    async def get_message(self, channel: ChannelDTO, msg_id: int) -> Optional[MediaDTO]:
        """Fetch a single message by ID."""
        if not self.client:
            return None

        message = await self.client.get_messages(channel.tg_id, ids=msg_id)
        if not message:
            return None

        # Convert to MediaDTO
        if not message.media:
            return None

        from telethon.tl.types import MessageMediaDocument
        if not isinstance(message.media, MessageMediaDocument):
            return None

        doc = message.media.document
        file_name = None
        duration_sec = None
        if doc.attributes:
            from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                elif isinstance(attr, DocumentAttributeVideo):
                    duration_sec = attr.duration

        reactions_dict = await self.fetch_reactions(message)
        comments_count = await self.fetch_comment_count(message)

        return MediaDTO(
            tg_msg_id=message.id,
            channel_tg_id=channel.tg_id,
            topic_tg_id=None,
            caption=message.text or message.message,
            file_name=file_name,
            mime=doc.mime_type,
            size_bytes=doc.size,
            duration_sec=duration_sec,
            date_posted=message.date,
            thumb_b64=None,
            reactions=reactions_dict,
            comments_count=comments_count,
            raw={}
        )

    async def fetch_thumb(self, message) -> Optional[str]:
        """Download smallest thumbnail; return base64 or None."""
        if not self.client or not message.media:
            return None

        try:
            thumb_bytes = await self.client.download_media(message, thumb=-1, file=bytes)
            if thumb_bytes:
                return base64.b64encode(thumb_bytes).decode("utf-8")
        except Exception:
            pass

        return None

    async def fetch_reactions(self, message) -> Optional[dict[str, int]]:
        """Extract reaction emoji → count from message.reactions."""
        if not hasattr(message, "reactions") or not message.reactions:
            return None

        reactions_dict = {}
        for result in message.reactions.results:
            emoji = result.reaction.emoticon if hasattr(result.reaction, "emoticon") else str(result.reaction)
            reactions_dict[emoji] = result.count

        return reactions_dict if reactions_dict else None

    async def fetch_comment_count(self, message) -> Optional[int]:
        """Extract comment count from message.replies."""
        if not hasattr(message, "replies") or not message.replies:
            return None

        return getattr(message.replies, "replies", None)

    def register_new_message_handler(self, callback) -> None:
        """Register a Telethon NewMessage handler (for realtime subscriptions).
        The callback is async and receives the event. Idempotent-ish: replaces
        any previously registered handler."""
        if not self.client:
            return
        old = getattr(self, "_nm_handler", None)
        if old is not None:
            try:
                self.client.remove_event_handler(old)
            except Exception:
                pass
        self._nm_handler = callback
        self.client.add_event_handler(callback, events.NewMessage())

    async def message_detail(self, channel_tg_id: int, msg_id: int, comment_limit: int = 30) -> Optional[dict]:
        """Full detail for one live message: meta, reactions, and comment thread.

        Comments are the message's reply thread (channel posts with a linked
        discussion group). Returns None if the message can't be resolved."""
        if not self.client:
            return None
        from telethon.tl.types import (
            MessageMediaDocument, DocumentAttributeFilename, DocumentAttributeVideo,
        )
        entity = await self._channel_input(channel_tg_id)
        msg = await self.client.get_messages(entity, ids=msg_id)
        if not msg:
            return None

        file_name = None
        duration_sec = None
        size_bytes = None
        mime = None
        if msg.media and isinstance(msg.media, MessageMediaDocument):
            doc = msg.media.document
            mime = doc.mime_type
            size_bytes = doc.size
            for attr in (doc.attributes or []):
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                elif isinstance(attr, DocumentAttributeVideo):
                    duration_sec = attr.duration

        reactions = await self.fetch_reactions(msg)
        comments = []
        try:
            async for c in self.client.iter_messages(entity, reply_to=msg_id, limit=comment_limit):
                if not (c.message or "").strip():
                    continue
                sender = await c.get_sender()
                author = None
                if sender is not None:
                    author = getattr(sender, "first_name", None) or getattr(sender, "title", None) \
                        or getattr(sender, "username", None)
                comments.append({
                    "id": c.id,
                    "author": author or "Unknown",
                    "text": c.message,
                    "date": c.date.isoformat() if c.date else None,
                })
        except Exception as e:
            # Channels without a linked discussion group raise; treat as no comments.
            print(f"[detail] comments unavailable for {channel_tg_id}/{msg_id}: {e!r}")

        return {
            "tg_msg_id": msg.id,
            "caption": msg.message or None,
            "file_name": file_name,
            "mime": mime,
            "size_bytes": size_bytes,
            "duration_sec": int(duration_sec) if duration_sec else None,
            "date_posted": msg.date.isoformat() if msg.date else None,
            "reactions": [{"emoji": k, "count": v} for k, v in (reactions or {}).items()],
            "comments": comments,
        }

    # ========================================================================
    # Task 6: Download with semaphore and progress callback
    # ========================================================================

    async def download_by_id(self, channel_tg_id: int, msg_id: int, dest_path: str, on_progress=None, offset: int = 0) -> str:
        """Resolve a message by (channel, id) then download it. The downloader
        stores ids, but download() needs the Telethon message object."""
        if not self.client:
            raise ValueError("Client not initialized")
        entity = await self._channel_input(channel_tg_id)
        msg = await self.client.get_messages(entity, ids=msg_id)
        if not msg:
            raise ValueError(f"Message {msg_id} not found")
        return await self.download(msg, dest_path, on_progress=on_progress, offset=offset)

    async def download(
        self,
        message,
        dest_path: str,
        on_progress=None,
        offset: int = 0,
    ) -> str:
        """
        Download media from message to dest_path using fast_telethon.
        Respects semaphore for concurrent downloads.
        Forwards progress callback.

        Args:
            message: Telethon message object with media.
            dest_path: Local path to save file.
            on_progress: Optional callback(bytes_done, bytes_total).

        Returns:
            dest_path if successful.
        """
        if not self.client or not message.media or not message.media.document:
            raise ValueError("Message must have a downloadable document")

        doc = message.media.document
        dest_path_obj = pathlib.Path(dest_path)
        dest_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Resume offset must be 4096-aligned for iter_download; drop the unaligned
        # tail of the partial file so we re-fetch from a clean boundary.
        offset = (offset // 4096) * 4096

        async with self.download_semaphore:
            if offset <= 0:
                # Fresh download: parallel fast path.
                with open(dest_path, "wb") as f:
                    await download_file(self.client, doc, f, progress_callback=on_progress)
            else:
                # Resume: single-stream from the byte offset, append into the partial.
                with open(dest_path, "r+b") as f:
                    f.seek(offset)
                    f.truncate()
                    async for chunk in self.client.iter_download(doc, offset=offset, request_size=512 * 1024):
                        f.write(chunk)
                        if on_progress:
                            r = on_progress(f.tell(), doc.size)
                            if inspect.isawaitable(r):
                                await r

        return dest_path
