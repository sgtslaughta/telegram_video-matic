from .db_utils import insert_into_table, TelegramChannel, Topic
from .db_utils import execute_db_command
from .db_utils import Message, MessageTags, DLFolder, Tags
from .tg_utils import TGAccount
from .log_utils import log
from .tag_utils import generate_tags
import asyncio
import tqdm
from datetime import datetime


async def pull_channels(tg_a: TGAccount, db_url: str):
    """
    Pull all channels from users Telegram and add them to the database.
    :param tg_a: TGAccount
    :param db_url: str
    :return:
    """
    if not db_url:
        log("Cannot pull channels, no database URL provided.", level="ERROR")
        return
    if not tg_a:
        log("Cannot pull channels, no TGAccount provided.", level="ERROR")
        return
    log("Pulling channels...", level="INFO")
    channels = await tg_a.get_channels()
    log(f"Found {len(channels)} channels.", level="INFO")
    for channel in channels:
        ch = channels[channel]
        x = {
            'channel_name': ch['name'],
            'ch_id': ch['id'],
            'raw_obj': ch['raw_obj'].stringify(),
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        insert_into_table(db_url, TelegramChannel, filter_column='ch_id', filter_value=x['ch_id'], **x)


async def pull_topics(tg_a: TGAccount, db_url: str, channel_name: str = None, channel_id: int = None):
    """
    Pull all topics from users Telegram and add them to the database.
    Args:
        tg_a:
        db_url:
        channel_name:
        channel_id:

    Returns:

    """
    if not channel_name and not channel_id:
        log("Cannot pull topics, no channel provided.", level="ERROR")
        return
    if channel_name and not channel_id:
        q_str = f"SELECT id, ch_id, channel_name FROM tg_channel WHERE channel_name='{channel_name}';"
        channel = execute_db_command(db_url, q_str)
        if not channel:
            log("Cannot pull topics, channel not found in database.", level="ERROR")
            return
        if len(channel) > 1:
            log("Cannot pull topics using channel_name, multiple channels found in database.", level="ERROR")
        db_ch_id = channel[0][0]
        ch_id = channel[0][1]
        ch_name = channel[0][2]
    if channel_id and not channel_name:
        q_str = f"SELECT id, channel_name FROM tg_channel WHERE ch_id={channel_id};"
        channel = execute_db_command(db_url, q_str)
        if not channel:
            log("Cannot pull topics, channel not found in database.", level="ERROR")
            return
        if len(channel) > 1:
            log("Cannot pull topics using channel_id, multiple channels found in database.", level="ERROR")
        db_ch_id = channel[0][0]
        ch_name = channel[0][1]
        ch_id = channel_id
    if not db_url:
        log("Cannot pull topics, no database URL provided.", level="ERROR")
        return
    if not tg_a:
        log("Cannot pull topics, no TGAccount provided.", level="ERROR")
        return
    log("Pulling topics...", level="INFO")
    topics = await tg_a.get_topics(channel_name=ch_id)
    log(f"Found {len(topics)} topics.", level="INFO")
    for topic in topics:
        t = topics[topic]
        x = {
            'topic_name': t['title'],
            'topic_id': t['id'],
            'raw_obj': t['raw_obj'].stringify(),
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'telegram_channel_id': db_ch_id
        }
        insert_into_table(db_url, Topic, filter_column='topic_id', filter_value=x['topic_id'], **x)


async def pull_videos(tg_a: TGAccount, db_url: str, channel_name: str = None, channel_id: int = None):
    """
    Pull all videos from users Telegram and add them to the database.
    Args:
        tg_a:
        db_url:
        channel_name:
        channel_id:

    Returns:

    """
    if not channel_name and not channel_id:
        log("Cannot pull videos, no channel provided.", level="ERROR")
        return
    if channel_name and not channel_id:
        q_str = f"SELECT id, ch_id, channel_name FROM tg_channel WHERE channel_name='{channel_name}';"
        channel = execute_db_command(db_url, q_str)
        if not channel:
            log("Cannot pull videos, channel not found in database.", level="ERROR")
            return
        if len(channel) > 1:
            log("Cannot pull videos using channel_name, multiple channels found in database.", level="ERROR")
        db_channel_id = channel[0][0]
        channel_id = channel[0][1]
        channel_name = channel[0][2]
    if channel_id and not channel_name:
        q_str = f"SELECT id, channel_name FROM tg_channel WHERE ch_id={channel_id};"
        channel = execute_db_command(db_url, q_str)
        if not channel:
            log("Cannot pull videos, channel not found in database.", level="ERROR")
            return
        if len(channel) > 1:
            log("Cannot pull videos using channel_id, multiple channels found in database.", level="ERROR")
        db_channel_id = channel[0][0]
        channel_name = channel[0][1]
    if not db_url:
        log("Cannot pull videos, no database URL provided.", level="ERROR")
        return
    if not tg_a:
        log("Cannot pull videos, no TGAccount provided.", level="ERROR")
        return
    q_str = f"SELECT id, topic_id FROM tg_topic WHERE telegram_channel_id={db_channel_id};"
    db_topics = execute_db_command(db_url, q_str)
    if not db_topics:
        log("No topics found in database.", level="ERROR")
        return
    topic_dict = {}
    for db_topic in db_topics:
        topic_dict[db_topic[1]] = db_topic[0]

    log("Pulling videos...", level="INFO")
    videos = await tg_a.get_all_videos(channel_name)
    log(f"Found {len(videos)} videos.", level="INFO")

    for video in videos:
        v = videos[video]
        try:
            t_id = topic_dict[v['topic_id']]
        except KeyError:
            t_id = None
            log("KeyError: 'topic_id' not found in video.", level="ERROR")

        x = {
            'name': v['title'],
            'msg_id': v['id'],
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'date_posted': v['date_posted'],
            'raw_obj': v['raw_obj'].stringify(),
            'telegram_channel_id': db_channel_id,
            'topic_id': t_id,
            'thumb': v['thumb']
        }
        insert_into_table(db_url, Message, filter_column='msg_id', filter_value=x['msg_id'], **x)


async def create_tags(tg_a: TGAccount, db_url: str):
    """
    Using the message titles, create tags for each message.
    Args:
        tg_a:
        db_url:

    Returns:

    """
    if not db_url:
        log("Cannot create tags, no database URL provided.", level="ERROR")
        return
    if not tg_a:
        log("Cannot create tags, no TGAccount provided.", level="ERROR")
        return
    log("Creating tags...", level="INFO")
    q_str = "SELECT id, name FROM tg_message;"
    db_messages = execute_db_command(db_url, q_str)
    if not db_messages:
        log("No messages found in database.", level="ERROR")
        return
    message_dict = {}
    for db_message in db_messages:
        message_dict[db_message[0]] = {
            'name': db_message[1],
            'tags': generate_tags(db_message[1])
        }
    for msg_id in message_dict:
        tags = message_dict[msg_id]['tags']
        for tag in tags:
            x = {'tag_name': tag}
            insert_into_table(db_url, Tags, **x)
            try:
                tag_id = execute_db_command(db_url, f"SELECT id FROM tg_tag WHERE tag_name={tag};")[0][0]
                y = {
                    'message_id': msg_id,
                    'tag_id': tag_id
                }
                insert_into_table(db_url, MessageTags, **y)
            except TypeError:
                continue


def show_tags(db_url: str, msg_id: int):
    """
    Generates the cross join to show all tags for a message.
    example: MSG, TAG1, TAG2, TAG3...
    Args:
        db_url:

    Returns:
    """
    if not db_url:
        log("Cannot show tags, no database URL provided.", level="ERROR")
        return
    tag_list = []
    q_str = f"SELECT tag_id FROM tg_message_tag WHERE message_id = {msg_id};"
    tags = execute_db_command(db_url, q_str)
    print(tags)
    if not tags:
        log("No tags found in database.", level="ERROR")
        return
    for tag in tags:
        q_str = f"SELECT tag_name FROM tg_tag WHERE id = {tag[0]};"
        tag_name = execute_db_command(db_url, q_str)
        tag_list.append(tag_name[0][0])
    return tag_list


async def run_all(tg_a: TGAccount, db_url: str, channel_name: str = None):
    """
    Run all functions in the module.
    Args:
        tg_a:
        db_url:

    Returns:

    """
    await pull_channels(tg_a, db_url)
    await pull_topics(tg_a, db_url, channel_name=channel_name)
    await pull_videos(tg_a, db_url, channel_name=channel_name)
    await create_tags(tg_a, db_url)


# url = "mysql+mysqlconnector://user:password@127.0.0.1:3306/moviesdb"
# tg = TGAccount(26748451, '00200de1624adc3900bfc3075665dd40')
# asyncio.run(run_all(tg, url, 'Rugby Try-Lights'))
