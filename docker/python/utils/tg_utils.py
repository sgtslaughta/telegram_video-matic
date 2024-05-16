"""
The functions in this file are used to interact with the Telegram API using the Telethon library.

"""

from telethon.sync import TelegramClient, functions, types
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import MessageMediaDocument
from telethon import errors
from utils.db_utils import DBHelper
import mysql
from mysql.connector.errors import IntegrityError
import sqlite3
from tqdm import tqdm
from .log_utils import log
import pathlib
import asyncio
import base64
from datetime import datetime
from functools import wraps


def ensure_authenticated(method):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if not self.client or not await self.client.is_user_authorized():
            await self.try_login()
        return await method(self, *args, **kwargs)
    return wrapper


class TGAccount:
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
        self.session_location = session_location
        self.auth_callback = auth_callback
        self.client = None

    async def try_login(self):
        self.client = TelegramClient(self.session_location, self.api_id, self.api_hash)
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                if self.auth_callback:
                    code = self.auth_callback()
                else:
                    code = input('Enter the code: ')
                await self.client.sign_in(self.phone, code)
        except KeyboardInterrupt as e:
            log(f"Error logging in: {e}", level="ERROR")

    @ensure_authenticated
    async def get_channels(self, limit=200):
        last_date = None
        channels = {}
        try:
            result = await self.client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer='username',
                limit=limit,
                hash=0
            ))
            for chat in result.chats:
                if isinstance(chat, types.Channel):
                    channels[chat.id] = {
                        'name': chat.title,
                        'id': chat.id,
                        'raw_obj': chat,
                    }
            if not channels:
                log("No channels found", level="WARN")
                return None
            return channels
        except sqlite3.OperationalError as e:
            log(f"Error getting channels: {e}", level="ERROR")
        except errors as e:
            log(f"Error getting channels: {e}", level="ERROR")
        except Exception as e:
            log(f"Error getting channels: {e}", level="ERROR")

    @ensure_authenticated
    async def get_topics(self, channel_name: str | int, limit: int = 100) -> dict | None:
        """
        Get the topics from a channel.
        :param channel_name: The name or ID of the channel
        :param limit: How many topics to get
        :return:
        """
        topics = {}
        if not channel_name:
            log("Channel name not provided", level="ERROR")
            return None
        try:
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
        except sqlite3.OperationalError as e:
            log(f"Error getting topics: {e}", level="ERROR")
        except errors.ChannelPrivateError as e:
            log(f"Error getting topics: {e}", level="ERROR")
        except Exception as e:
            log(f"Error getting topics: {e}", level="ERROR")

    async def get_video_mt(self, message,
                           db_url,
                           client,
                           progress=0,
                           total=0,
                           callback=None,
                           topic_dict=None,
                           channel_dict=None,
                           pool=None):
        # Check if the message has media
        if message.media:
            # Check if the media type is a document (video, gif, etc.)
            if isinstance(message.media, MessageMediaDocument):
                # If it's a video, process the message
                if message.media.document.mime_type.startswith('video/'):
                    # Do something with the video message
                    if message.reply_to:
                        if message.reply_to.forum_topic:
                            if callback:
                                progress += 1
                                msg = f"{progress}/{total}: {message.message}"
                                callback(progress, total, msg)
                            try:
                                f_name = message.media.document.attributes[1].file_name
                            except AttributeError:
                                return
                            except IndexError:
                                return
                            thumb = await client.download_media(message, thumb=-1, file=bytes)
                            if thumb:
                                thumb_base64 = base64.b64encode(thumb).decode('utf-8')
                            else:
                                thumb_base64 = None
                            # Mismatch on the Ids, need to fix this (tg ch id and topic id)
                            topic_id = None
                            channel_id = None
                            try:
                                topic_id = topic_dict[int(message.reply_to.reply_to_msg_id)]
                            except KeyError:
                                if message.reply_to.reply_to_msg_id not in topic_dict:
                                    topic_id = None
                            try:
                                channel_id = channel_dict[message.peer_id.channel_id]
                            except KeyError:
                                if message.peer_id.channel_id not in channel_dict:
                                    channel_id = None
                            try:
                                x = {
                                    'name': f_name,
                                    'msg_id': message.id,
                                    'topic_id': topic_id,
                                    'tg_ch_id': channel_id,
                                    'date_posted': message.date,
                                    'raw_obj': message.stringify(),
                                    "thumb": thumb_base64,
                                    'date_added': datetime.now(),
                                }
                            except KeyError:
                                log(f"KeyError: {message.id}", level="ERROR")
                                return
                            # insert_into_table(db_url, Message, filter_column='msg_id', filter_value=x['msg_id'],
                            #                   **x)
                            self.insert_video(x, pool)

    @staticmethod
    async def grab_file(client, message, idx, dl_path='./', callback=None) -> None:
        """
        Download a file from a Telegram message.
        :param client: The Telegram client
        :param message: The message containing the file
        :param idx: The index of the message used to position the terminal progress bar
        :param dl_path: The path to download the file to, defaults to the current directory
        :param callback: Optional callback function to update the progress
        :return: None
        """
        def progress_bar(downloaded_bytes, total_bytes):
            if total_bytes:
                diff_since_last = downloaded_bytes - progress_bar.n
                progress_bar.update(diff_since_last)
        total_b = message.file.size
        if not callback:
            progress_bar = tqdm(total=total_b, unit='B', unit_scale=True, unit_divisor=1024, desc=message.file.name,
                                 leave=False, position=idx)
            callback = progress_bar

        if not pathlib.Path(dl_path).exists():
            log(f"Download path does not exist: {dl_path}", level="ERROR")
            return None
        try:
            path = await client.download_media(message, dl_path, progress_callback=callback)
        except KeyboardInterrupt as e:
            log(f"Error grabbing video: {e}", level="ERROR")

    async def get_messages_by_id(self, msg_ids: list, channel_name: str) -> list:
        """
        Get a telethon Telegram message object by ID.
        :param msg_ids: list - the message IDs
        :param channel_name: str - the channel name
        :return: None
        """
        try:
            messages = []
            async with TelegramClient(self.session_location, self.api_id, self.api_hash) as client:
                async for msg in client.iter_messages(channel_name, ids=msg_ids):
                    messages.append(msg)
            return messages
        except [Exception] as e:
            log(f"Error getting message by ID: {e}", level="ERROR")

    async def multi_download(self, message_list: list, dl_path: str = './') -> None:
        """
        Download media concurrently using asyncio.
        :param message_list: list - of the telethon Telegram message objects containing the videos
        :param dl_path: str - the path to download the videos to
        :return:
        """
        async with TelegramClient(self.session_location, self.api_id, self.api_hash) as client:
            video_tasks = []
            for idx, message in enumerate(message_list):
                video_tasks.append(self.grab_file(client, message, idx, dl_path))

            # Run the grab_video tasks concurrently
            await asyncio.gather(*video_tasks)
