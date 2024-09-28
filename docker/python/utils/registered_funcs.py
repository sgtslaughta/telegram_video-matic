from .file_utils import scan_video_directory
from .log_utils import log
from .db_utils import DBHelper, Message, TelegramChannel, Topic
from .tg_utils import TGAccount
from .data_utils import pull_messages
from .vars_init import get_vars
from os import environ
import asyncio


def print_thing(name):
    print("\tHERE WE GO! ", name)


def test_func(name):
    print(f"\tTest func here baby! {name}")


def scan_files(directory):
    pass
    # print(f"Scanning directory: {directory}")
    videos = scan_video_directory(directory)
    print(f"Found {len(videos)} videos in {directory}")


def update_topic_msgs(ch_topic_id):
    asyncio.run(look_for_updates_on_tg(ch_topic_id))


async def look_for_updates_on_tg(ch_topic_id):
    get_vars()
    ch_id, topic_id = ch_topic_id.split('_')
    try:
        ch_id = int(ch_id)
        topic_id = int(topic_id)
    except ValueError:
        print("Invalid channel id or topic id")
        return
    log(f"Looking for updates on channel {ch_id} for topic {topic_id}", 'INFO')
    if environ.get('DB_URL') is None:
        log("DB_URL not found in environment variables", 'ERROR')
        return
    db_url = environ.get('DB_URL')
    if environ.get('API_ID') is None or environ.get('API_HASH') is None or environ.get('PHONE') is None:
        log("API_ID, API_HASH or PHONE not found in environment variables", 'ERROR')
        return
    api_id = int(environ.get('API_ID'))
    api_hash = environ.get('API_HASH')
    phone = environ.get('PHONE')
    dbc = DBHelper(db_url)
    tg = TGAccount(api_id, api_hash, phone)
    last_msg = await dbc.get_highest_by(Message, Message.topic_id == topic_id, Message.date_posted)
    ch_name = await dbc.query_with_filter(TelegramChannel, TelegramChannel.id == ch_id)
    ch_name = ch_name[0].ch_name
    topic_name = await dbc.query_with_filter(Topic, Topic.id == topic_id)
    topic_name = topic_name[0].topic_name
    kwargs = {
        'tg_a': tg,
        'dbh': dbc,
        'channel_name': ch_name,
        'topic': topic_name,
        'progress_callback': None,
        'offset_date': None,
        'limit': None,
        'reverse': False,
    }
    if last_msg:
        kwargs['offset_id'] = last_msg.msg_id
        kwargs['reverse'] = True
        # await pull_messages(tg, dbc, ch_name, progress_callback=None, topic=topic_name, limit=None, reverse=False)
    log(f"Checking for TG updates ['{ch_name}':'{topic_name}']", 'INFO')
    await pull_messages(**kwargs)


