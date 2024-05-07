from telethon.sync import TelegramClient, functions, types
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import InputPeerEmpty
from telethon import errors
from tqdm import tqdm
from log_utils import log
import pathlib
import threading
import asyncio
import aiohttp
from fast_telethon import download_file
import time

class Timer:
    def __init__(self, time_between=2):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False


class TGAccount:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash

    def get_channels(self, limit=200):
        last_date = None
        channels = {}
        try:
            with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = client(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer='username',
                    limit=limit,
                    hash=0
                ))
                for chat in result.chats:
                    if type(chat) is types.Channel:
                        channels[chat.id] = {
                            'name': chat.title,
                            'id': chat.id,
                            'raw_obj': chat,
                        }
                if not channels:
                    log("No channels found", level="WARN")
                    return None
                return channels
        except errors as e:
            log(f"Error getting channels: {e}", level="ERROR")

    def get_topics(self, channel_name=None, limit=100):
        try:
            topics = {}
            with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = client(functions.channels.GetForumTopicsRequest(
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
                        'raw': topic,
                    }
                return topics
        except errors as e:
            log(f"Error getting topics: {e}", level="ERROR")

    def get_chats_by_topic(self, channel_name, topic_id, ch_limit=100, msg_limit=100):
        try:
            chats = {}
            with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = client(GetDialogsRequest(
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
        except errors as e:
            log(f"Error getting chats by topic: {e}", level="ERROR")

    def get_videos_by_topic(self, channel_name, topic_id, ch_limit=100, msg_limit=100):
        try:
            videos = {}
            with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = client(GetDialogsRequest(
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
                                    if msg.media:
                                        videos[msg.id] = {
                                            'text': msg.message,
                                            'id': msg.id,
                                            'raw_obj': msg,
                                        }
            if not videos:
                log(f"No videos found for topic {topic_id}", level="WARN")
                return None
            return videos
        except errors as e:
            log(f"Error getting videos by topic: {e}", level="ERROR")

    async def grab_video(self, semaphore, client, message, dl_path='./'):
        if not pathlib.Path(dl_path).exists():
            log(f"Download path does not exist: {dl_path}", level="ERROR")
            return None

        try:
            async with semaphore:
                with open(dl_path + message.file.name, 'wb') as f:
                    await download_file(client, message.document, f)

        except KeyboardInterrupt as e:
            log(f"Error grabbing video: {e}", level="ERROR")

    def get_message_by_id(self, msg_id, channel_name):
        try:
            with TelegramClient('name', self.api_id, self.api_hash) as client:
                result = client(GetDialogsRequest(
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
        except errors as e:
            log(f"Error getting message by ID: {e}", level="ERROR")



api_id = 26748451
api_hash = '00200de1624adc3900bfc3075665dd40'
tg = TGAccount(api_id, api_hash)
channels = tg.get_channels()
# for ch in channels:
#     topics = tg.get_topics(ch)
#     for key, value in topics.items():
#         print(key, value['title'])
# chats = tg.get_chats_by_topic('Rugby Try-Lights', 8837)
# print(chats)
videos = tg.get_videos_by_topic('Rugby Try-Lights', 8837)
# tg.grab_video(9222, 'Rugby Try-Lights')
# tg.grab_video(9221, 'Rugby Try-Lights')
msg1 = tg.get_message_by_id(9222, 'Rugby Try-Lights')
msg2 = tg.get_message_by_id(9221, 'Rugby Try-Lights')


async def test(tga):
    semaphore = asyncio.Semaphore(5)
    async with TelegramClient('name', api_id, api_hash) as client:
        messages_to_download = [
            msg1,
            msg2,
            # Add more message objects as needed
        ]
        # Define the list of videos you want to download concurrently
        video_tasks = []
        for message in messages_to_download:
            video_tasks.append(tga.grab_video(semaphore, client, message, './'))

        # Run the grab_video tasks concurrently
        await asyncio.gather(*video_tasks)

print(videos)
asyncio.run(test(tg))

# for key, value in videos.items():


# async def main(tga):
#     # Define the list of videos you want to download concurrently
#     videos_to_download = [
#         (9222, 'Rugby Try-Lights'),
#         (9221, 'Rugby Try-Lights'),
#         # Add more video IDs and channel names here if needed
#     ]
#
#     semaphore = asyncio.Semaphore(5)
#
#     # Create tasks for each video to be downloaded concurrently
#     tasks = []
#     for video_info in videos_to_download:
#         tasks.append(tga.grab_video(semaphore, *video_info))
#
#     # Run the tasks concurrently
#     await asyncio.gather(*tasks)



