"""
The functions in this file are used to interact with the Telegram API using the Telethon library.

"""

from telethon.sync import TelegramClient, functions, types
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import MessageMediaDocument
import sqlite3
from tqdm import tqdm
from .log_utils import log
import pathlib
import asyncio
from .fast_telethon import download_file
import base64


class TGAccount:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash

    async def get_channels(self, limit=200):
        last_date = None
        channels = {}
        async with TelegramClient('name', self.api_id, self.api_hash) as client:  # Use async with
            result = await client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer='username',
                limit=limit,
                hash=0
            ))
            for chat in result.chats:
                if isinstance(chat, types.Channel):  # Use isinstance() instead of type()
                    channels[chat.id] = {
                        'name': chat.title,
                        'id': chat.id,
                        'raw_obj': chat,
                    }
            if not channels:
                log("No channels found", level="WARN")
                return None
            return channels

    async def get_topics(self, channel_name=None, limit=100):
        topics = {}
        async with TelegramClient('name', self.api_id, self.api_hash) as client:
            result = await client(functions.channels.GetForumTopicsRequest(
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

    async def get_chats_by_topic(self, channel_name, topic_id, ch_limit=100, msg_limit=100):
        try:
            chats = {}
            async with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = await client(GetDialogsRequest(
                    offset_id=0,
                    offset_date=None,
                    offset_peer='username',
                    limit=ch_limit,
                    hash=0
                ))
                for channel in result.chats:
                    if type(channel) is types.Channel and channel.title == channel_name:
                        messages = client.get_messages(channel, limit=msg_limit)
                        for msg in messages:
                            if msg.reply_to:
                                if msg.reply_to.reply_to_msg_id == topic_id:
                                    chats[msg.id] = {
                                        'text': msg.text,
                                        'id': msg.id,
                                        'raw_obj': msg,
                                    }
            if not chats:
                log(f"No chats found for topic {topic_id}", level="WARN")
                return None
            return chats
        except [Exception] as e:
            log(f"Error getting chats by topic: {e}", level="ERROR")

    async def get_all_videos(self, channel_name):
        videos = {}
        if not channel_name:
            log("Channel name not provided", level="ERROR")
            return None
        async with TelegramClient('name', self.api_id, self.api_hash) as client:
            log("Fetching total messages...")
            dialogs = await client.get_dialogs()
            for dialog in dialogs:
                if dialog.title == channel_name:
                    try:
                        if dialog.entity.megagroup:
                            total = int(dialog.message.id)
                            break
                    except AttributeError:
                        pass
            log(f"Attempting to fetch video messages from {total} total messages, this may take some time...")
            pbar = tqdm(total=total, desc=f"Looking for videos in: {channel_name}")
            async for message in client.iter_messages(channel_name):
                pbar.update(1)
                # Check if the message has media
                if message.media:
                    # Check if the media type is a document (video, gif, etc.)
                    if isinstance(message.media, MessageMediaDocument):
                        # If it's a video, process the message
                        if message.media.document.mime_type.startswith('video/'):
                            # Do something with the video message
                            if message.reply_to:
                                if message.reply_to.forum_topic:
                                    try:
                                        f_name = message.media.document.attributes[1].file_name
                                    except AttributeError:
                                        continue
                                    except IndexError:
                                        continue
                                    thumb = await client.download_media(message, thumb=-1, file=bytes)
                                    if thumb:
                                        thumb_base64 = base64.b64encode(thumb).decode('utf-8')
                                    else:
                                        thumb_base64 = None
                                    videos[message.id] = {
                                        'title': message.message,
                                        'id': message.id,
                                        'topic_id': message.reply_to.reply_to_msg_id,
                                        'ch_id': message.peer_id.channel_id,
                                        'file_name': f_name,
                                        'date_posted': message.date,
                                        'raw_obj': message,
                                        "thumb": thumb_base64
                                    }
        if not videos:
            log(f"No videos found for channel {channel_name}", level="WARN")
            return None
        return videos

    async def get_videos_by_topic(self, channel_name, topic_id, ch_limit=100, msg_limit=2000):
        videos = {}
        if not channel_name or not topic_id:
            log("Channel name or topic ID not provided", level="ERROR")
            return None
        async with TelegramClient('name', self.api_id, self.api_hash) as client:
            result = await client(GetDialogsRequest(
                offset_id=0,
                offset_date=None,
                offset_peer='username',
                limit=ch_limit,
                hash=0
            ))
            if not result:
                log("No dialogs found", level="ERROR")
                return None
            for channel in result.chats:
                if type(channel) is types.Channel and channel.title == channel_name:
                    messages = await client.get_messages(channel, limit=msg_limit)
                    for msg in messages:
                        if msg.reply_to:
                            if msg.reply_to.reply_to_msg_id == topic_id:
                                try:
                                    if msg.media.document:
                                        videos[msg.id] = {
                                            'text': msg.message,
                                            'id': msg.id,
                                            'raw_obj': msg,
                                        }
                                except AttributeError:
                                    pass
        if not videos:
            log(f"No videos found for topic {topic_id}", level="WARN")
            return None
        return videos

    async def grab_video(self, semaphore, client, message, idx, dl_path='./'):
        total_b = message.file.size
        progress_bart = tqdm(total=total_b, unit='B', unit_scale=True, unit_divisor=1024, desc=message.file.name,
                             leave=False, position=idx)

        def progress_bar(downloaded_bytes, total_bytes):
            if total_bytes:
                diff_since_last = downloaded_bytes - progress_bart.n
                progress_bart.update(diff_since_last)

        if not pathlib.Path(dl_path).exists():
            log(f"Download path does not exist: {dl_path}", level="ERROR")
            return None

        try:
            async with semaphore:
                with open(dl_path + message.file.name, 'wb') as f:
                    await download_file(client, message.document, f, progress_callback=progress_bar)

        except [Exception] as e:
            log(f"Error grabbing video: {e}", level="ERROR")

    async def get_message_by_id(self, msg_id: int, channel_name: str) -> None:
        """
        Get a telethon Telegram message object by ID.
        :param msg_id: int - the message ID
        :param channel_name: str - the channel name
        :return: None
        """
        try:
            async with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = await client(GetDialogsRequest(
                    offset_id=0,
                    offset_date=None,
                    offset_peer='username',
                    limit=100,
                    hash=0
                ))
                for channel in result.chats:
                    if type(channel) is types.Channel and channel.title == channel_name:
                        messages = client.get_messages(channel, limit=100)
                        for msg in messages:
                            if msg.id == msg_id:
                                return msg
        except [Exception] as e:
            log(f"Error getting message by ID: {e}", level="ERROR")

    async def threaded_dl(self, message_list: list, dl_path: str = './') -> None:
        """
        Download videos concurrently using asyncio.
        :param message_list: list - of the telethon Telegram message objects containing the videos
        :param dl_path: str - the path to download the videos to
        :return:
        """
        semaphore = asyncio.Semaphore(5)
        async with TelegramClient('name', self.api_id, self.api_hash) as client:
            video_tasks = []
            for idx, message in enumerate(message_list):
                video_tasks.append(self.grab_video(semaphore, client, message, idx, dl_path))

            # Run the grab_video tasks concurrently
            await asyncio.gather(*video_tasks)
