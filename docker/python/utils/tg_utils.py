"""
The functions in this file are used to interact with the Telegram API using the Telethon library.

"""

import asyncio
import base64
import os.path
import pathlib
from datetime import datetime
from functools import wraps
from typing import Any, Coroutine, Tuple, List, Iterable
from telethon.sync import TelegramClient, functions, types
from telethon.tl.functions.channels import GetFullChannelRequest, \
    GetMessagesRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputMessagesFilterDocument, \
    InputMessagesFilterPhotos, InputMessagesFilterVideo
from telethon.tl.types import InputMessagesFilterMusic, InputMessagesFilterUrl, \
    InputMessagesFilterVoice
from telethon.tl.types import (MessageMediaDocument, InputChannel,
                               InputPeerSelf)
from tqdm import tqdm

from .log_utils import log

p_bars = {}

def catch_and_log_errors(method: callable) -> callable:
    """
    Catch and log errors that occur in the method.
    :param method: The method to call
    :return: callable The wrapped method
    """

    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        try:
            return await method(self, *args, **kwargs)
        except Exception as e:
            log(f"An error occurred in {method.__name__}: {e}, {e.__class__}", level="ERROR")
            return None

    return wrapper


def ensure_authenticated(method: callable) -> callable:
    """
    Ensure that the client is authenticated before calling the method.
    :param method: The method to call
    :return: callable The wrapped method
    """

    @catch_and_log_errors
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if not self.client or not await self.client.is_user_authorized():
            try:
                await self.try_login()
            except Exception as e:
                log(f"An error occurred during authentication: {e}", level="ERROR")
                return None
        return await method(self, *args, **kwargs)

    return wrapper


class TGFilters:
    """
    A class to hold the message filters.
    """
    FILTER_DOCUMENT = InputMessagesFilterDocument
    FILTER_PHOTO = InputMessagesFilterPhotos
    FILTER_VIDEO = InputMessagesFilterVideo
    FILTER_MUSIC = InputMessagesFilterMusic
    FILTER_URL = InputMessagesFilterUrl
    FILTER_VOICE = InputMessagesFilterVoice


class TGAccount(TGFilters):
    """
    A class to interact with a Telegram account.
    :param api_id: int - the Telegram API ID
    :param api_hash: str - the Telegram API hash
    :param phone: str - the phone number associated with the account
    :param session_location: str - the location to store the session file
    """

    def __init__(self,
                 api_id: int,
                 api_hash: str,
                 phone: str = None,
                 session_location: str = 'name',
                 auth_callback=None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_location = os.path.abspath(session_location)
        self.auth_callback = auth_callback
        self.client = None
        self.code = None
        self.phone_code_hash = None

    async def try_login(self, callback=None):
        self.client = TelegramClient(self.session_location, self.api_id,
                                     self.api_hash)
        await self.client.start(phone=self.phone, code_callback=callback)
        if not await self.client.is_user_authorized():
            print(self.auth_callback)
            if self.auth_callback:
                code = await self.auth_callback()
            else:
                code = input('Enter the code: ')
            await self.client.sign_in(phone=self.phone, code=code)

    @ensure_authenticated
    async def get_channels(self, limit=200) -> dict | None:
        """
        Get the channels that the account is a member of.
        Args:
            limit: The max number of channels to get

        Returns: dict The channels that the account is a member of

        """
        last_date = None
        channels = {}
        result = await self.client(GetDialogsRequest(
            offset_date=last_date,
            offset_id=0,
            offset_peer=await self.client.get_input_entity(InputPeerSelf()),
            limit=limit,
            hash=0
        ))
        for chat in result.chats:
            if isinstance(chat, types.Channel):
                channels[chat.id] = {
                    'name': chat.title,
                    'id': chat.id,
                    'raw_obj': await self.get_channel_full(chat),
                }
        if not channels:
            log("No channels found", level="WARN")
            return None
        return channels

    @ensure_authenticated
    async def get_topics(self, channel_name: InputChannel, limit: int = 100) -> dict | None:
        """
        Get the topics from a channel.
        :param channel_name: The name or ID of the channel
        :param limit: How many topics to get
        :return: dict The topics from the channel or None if there are no topics
        """
        topics = {}
        if not channel_name:
            log("Channel name not provided", level="ERROR")
            return None
        result = await self.client(functions.channels.GetForumTopicsRequest(
            channel=channel_name,
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=limit,
        ))
        for topic in result.topics:
            topics[topic.id] = {
                'title': topic.title,
                'id': topic.id,
                'raw_obj': topic,
            }
        return topics

    @ensure_authenticated
    async def get_media_message(self, message, callback=None):
        # Check if the message has media
        if not message.media:
            log(f"No media found in message: {message.id}", level="WARN")
            return None
        if message.media:
            # Check if the media type is a document (video, gif, etc.)
            if isinstance(message.media, MessageMediaDocument):
                msgs = {}
                try:
                    f_name = message.media.document.attributes[1].file_name
                except AttributeError:
                    return
                except IndexError:
                    return
                thumb = await self.client.download_media(message, thumb=-1, file=bytes)
                if thumb:
                    thumb_base64 = base64.b64encode(thumb).decode('utf-8')
                else:
                    thumb_base64 = None
                x = {
                    'name': f_name,
                    'msg_id': message.id,
                    'date_posted': message.date,
                    'raw_obj': message.stringify(),
                    "thumb": thumb_base64,
                    'date_added': datetime.now(),
                }


    @ensure_authenticated
    async def get_messages_by_id(self, msg_ids: list, channel_name: str) -> list:
        """
        Get a telethon Telegram message object by ID.
        :param msg_ids: list - the message IDs
        :param channel_name: str - the channel name
        :return: None
        """
        log(f"Getting {len(msg_ids)} messages by ID: {msg_ids}", level="INFO")
        peer = await self.get_peer(channel_name)
        msgs = await self.client(GetMessagesRequest(channel=peer, id=msg_ids))
        return msgs

    # @ensure_authenticated
    async def grab_file(self, message, progress_callback=None) -> None:
        """
        Download a file from a Telegram message.
        """

        dl_path = message['path']
        msg = message['msg_obj']
        file_name = message['file_name']
        total_b = msg.media.document.size

        if not pathlib.Path(dl_path).exists():
            pathlib.Path(dl_path).mkdir(parents=True)
        full_path = os.path.abspath(os.path.join(dl_path, file_name))
        if os.path.exists(full_path):
            log(f"File already exists: {dl_path}/{file_name}", level="INFO")
            return None
        if pathlib.Path(full_path).exists():
            log(f"File already exists: {dl_path}/{file_name}", level="INFO")
            return None

        log(f"Downloading file: '{full_path}' [{round(total_b / (1024 * 1024), 2)}MB]", level="INFO")
        await self.client.download_media(msg, full_path, progress_callback=progress_callback)

    async def progress(tasks: Iterable[Coroutine], **pbar_kws: Any) -> List[Any]:
        """Runs async tasks with a progress bar and returns an ordered result."""

        if not tasks:
            return []

        async def tup(idx: int, task: Coroutine) -> Tuple[int, Any]:
            """Returns the index and result of a task."""
            return idx, await task

        _tasks = [tup(i, t) for i, t in enumerate(tasks)]
        pbar = tqdm(asyncio.as_completed(_tasks), total=len(_tasks), **pbar_kws)
        res = [await t for t in pbar]
        return [r[1] for r in sorted(res, key=lambda r: r[0])]

    @ensure_authenticated
    # @ensure_authenticated
    async def multi_download(self, message_list: list, concurrent_amt: int = 5):
        """
        Download media concurrently using asyncio.
        """
        semaphore = asyncio.Semaphore(concurrent_amt)

        async def sem_task(message):
            async with semaphore:
                await self.grab_file(message)

        video_tasks = [sem_task(message) for message in message_list]

        await asyncio.gather(*video_tasks)

    @ensure_authenticated
    async def get_messages(self,
                           limit: int | None = 100,
                           offset_id: int = 0,
                           offset_date: datetime = None,
                           search_str: str = None,
                           msg_filter: str = None,
                           min_id: int = 0,
                           max_id: int = 0,
                           entity: str = None,
                           callback: callable = None,
                           reverse=False,
                           reply_to=None) -> list:
        """
        Get messages from a channel.
        Args:
            limit: The max number of messages to get
            offset_id: The message ID to start from
            offset_date: The date to start from
            search_str: The string to search for
            msg_filter: The message filter to apply
            min_id: The min message ID
            max_id: The max message ID
            entity: str | Entity object The entity to get messages from (channel name/id, user, etc.)
            callback: callable The callback function to report how many messages have been retrieved.
            reverse: bool Whether to reverse the order of the messages
                RETURNS int The length of the messages list
            reply_to: int The message ID to reply to

        References: https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
        Returns:

        """
        entity = await self.get_peer(entity)
        messages = []
        step = 0

        async for msg in self.client.iter_messages(limit=limit,
                                                   offset_id=offset_id,
                                                   offset_date=offset_date,
                                                   search=search_str,
                                                   filter=msg_filter,
                                                   min_id=min_id,
                                                   max_id=max_id,
                                                   entity=entity,
                                                   reverse=reverse,
                                                   reply_to=reply_to):
            messages.append(msg)
            step += 1
            if callback:
                callback(step, len(messages), f"Video #{step} downloaded")
        return messages

    @ensure_authenticated
    async def get_peer(self, entity):
        """
        Get a peer object.
        Args:
            entity:

        Returns:

        """
        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            if dialog.name == entity or dialog.id == entity:
                return await self.client.get_entity(dialog)

    @ensure_authenticated
    async def get_channel_full(self, entity: InputChannel = None,
                               ch_name_id: str | int = None) -> dict | None:
        """
        Get the full channel object. Use the read_outbox_max_id to get the latest message ID/ count.
        Args:
            entity: InputChannel type; The channel entity
            ch_name_id: str | int The channel name or ID

        Returns: The full channel object

        """
        if not entity and not ch_name_id:
            log("No entity or channel name provided", level="ERROR")
            return None
        if ch_name_id and not entity:
            entity = await self.get_peer(ch_name_id)
            return await self.client(GetFullChannelRequest(channel=entity))
        return await self.client(GetFullChannelRequest(channel=entity))


    @ensure_authenticated
    async def get_logo_photo(self, channel: InputChannel) -> bytes | None:
        """
        Get the logo of a channel.
        Args:
            channel: InputChannel The channel entity

        Returns: bytes The logo of the channel

        """
        if not channel:
            log("No channel provided", level="ERROR")
            return None
        return await self.client.download_profile_photo(channel, file=bytes)

    @ensure_authenticated
    async def get_forumntopic(self, channel, topic_id):
        channel = await self.get_peer(channel)
        return await self.client(functions.channels.GetForumTopicsByIDRequest(
            channel=channel,
            topics=[topic_id]
        ))