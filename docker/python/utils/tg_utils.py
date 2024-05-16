"""
The functions in this file are used to interact with the Telegram API using the Telethon library.

"""
from utils.db_utils import DBHelper
from telethon.sync import TelegramClient, functions, types
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import MessageMediaDocument
from telethon.tl.types import InputMessagesFilterDocument, InputMessagesFilterPhotos, InputMessagesFilterVideo
from telethon.tl.types import InputMessagesFilterMusic, InputMessagesFilterUrl, InputMessagesFilterVoice
from telethon import errors
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
                # # Request the phone code
                # phone_code_hash = await self.client.send_code_request(self.phone)
                # print(f"Phone code hash: {phone_code_hash}")
                if self.auth_callback:
                    # Pass the phone code hash to the auth callback if available
                    code = self.auth_callback()
                else:
                    code = input('Enter the code: ')
                # Sign in using the received phone code hash and the entered code
                await self.client.sign_in(phone=self.phone, code=code)
        except KeyboardInterrupt as e:
            log(f"Error logging in: {e}", level="ERROR")

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
        :return: dict The topics from the channel or None if there are no topics
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
                try:
                    x = {
                        'name': f_name,
                        'msg_id': message.id,
                        'date_posted': message.date,
                        'raw_obj': message.stringify(),
                        "thumb": thumb_base64,
                        'date_added': datetime.now(),
                    }
                except Exception as e:
                    log(f"Error getting media message: {e}", level="ERROR")

    @ensure_authenticated
    async def grab_file(self, message, idx, dl_path='./', callback=None) -> None:
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
            path = await self.client.download_media(message, dl_path, progress_callback=callback)
        except KeyboardInterrupt as e:
            log(f"Error grabbing video: {e}", level="ERROR")

    @ensure_authenticated
    async def get_messages_by_id(self, msg_ids: list, channel_name: str) -> list:
        """
        Get a telethon Telegram message object by ID.
        :param msg_ids: list - the message IDs
        :param channel_name: str - the channel name
        :return: None
        """
        try:
            messages = []
            async for msg in self.client.iter_messages(channel_name, ids=msg_ids):
                messages.append(msg)
            return messages
        except [Exception] as e:
            log(f"Error getting message by ID: {e}", level="ERROR")

    @ensure_authenticated
    async def multi_download(self, message_list: list, dl_path: str = './') -> None:
        """
        Download media concurrently using asyncio.
        :param message_list: list - of the telethon Telegram message objects containing the videos
        :param dl_path: str - the path to download the videos to
        :return:
        """
        video_tasks = []
        for idx, message in enumerate(message_list):
            video_tasks.append(self.grab_file(message, idx, dl_path))

            # Run the grab_video tasks concurrently
        await asyncio.gather(*video_tasks)

    @ensure_authenticated
    async def get_messages(self,
                           limit: int = 100,
                           offset_id: int = 0,
                           offset_date: int = None,
                           search_str: str = None,
                           msg_filter: str = None,
                           min_id: int = 0,
                           max_id: int = 0,
                           entity: str = None) -> list:
        """
        Get messages from a channel.
        Args:
            limit:
            offset_id:
            offset_date:
            search_str:
            msg_filter:
            min_id:
            max_id:
            entity:

        References: https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.messages.MessageMethods.iter_messages
        Returns:

        """
        try:

            messages = []
            async for msg in self.client.iter_messages(limit=limit,
                                                       offset_id=offset_id,
                                                       offset_date=offset_date,
                                                       search=search_str,
                                                       filter=msg_filter,
                                                       min_id=min_id,
                                                       max_id=max_id,
                                                       entity=entity):
                messages.append(msg)
            return messages
        except Exception as e:
            log(f"Error getting messages: {e}", level="ERROR")

    @ensure_authenticated
    async def get_peer(self, entity):
        """
        Get a peer object.
        Args:
            entity:

        Returns:

        """
        try:
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                if dialog.name == entity:
                    return dialog.id
        except Exception as e:
            log(f"Error getting peer: {e}", level="ERROR")
