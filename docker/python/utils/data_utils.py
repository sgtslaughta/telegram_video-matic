import asyncio
import base64
from datetime import datetime

from mysql.connector.errors import IntegrityError
from psycopg2 import pool
from sqlalchemy import or_

from .db_utils import DBHelper, TelegramChannel, Topic, Message
from .log_utils import log
from .tag_utils import generate_tags
from .tg_utils import TGAccount


async def pull_channels(tg_a: TGAccount, dbh: DBHelper, callback=None):
    """
    Pull all channels from users Telegram and add them to the database.
    :param tg_a: TGAccount
    :param dbh: str
    :param callback: An optional callback function to update the progress.
    :return:
    """
    total_steps = 3
    step = 1
    if callback:
        callback(step, total_steps, "1: Validating inputs...")
    if not dbh:
        log("Cannot pull channels, no database URL provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.1 Cannot pull channels, no database URL provided...FAILED")
        return
    if not tg_a:
        log("Cannot pull channels, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.2 Cannot pull channels, no TGAccount provided...FAILED")
        return
    log("Pulling channels...", level="INFO")
    step += 1
    if callback:
        callback(step, total_steps, "2: Getting channels from Telegram...")
    channels = await tg_a.get_channels()
    if not channels:
        log("No channels found.", level="ERROR")
        if callback:
            callback(step, total_steps, "2.1 No channels found...FAILED")
        return
    log(f"Found {len(channels)} channels.", level="INFO")
    step += 1
    ch_step = 1
    data = []
    for channel in channels:
        if callback:
            callback(step, total_steps, f"3: Inserting channel {ch_step}/{len(channels)} into database...")
        ch = channels[channel]
        x = {
            'ch_name': ch['name'],
            'ch_id': ch['id'],
            'date_added': datetime.now(),
            'date_last_updated': datetime.now()
        }
        ch = TelegramChannel(**x)
        await dbh.add_record(ch)
        ch_step += 1


async def pull_topics(tg_a: TGAccount,
                      dbh: DBHelper,
                      channel_name: str = None,
                      channel_id: int = None,
                      callback=None):
    """
    Pull all topics from users Telegram and add them to the database.
    :param tg_a:
    :param db_url:
    :param channel_name:
    :param channel_id:
    :param callback:
    :return:
    """
    total_steps = 3
    step = 1
    if callback:
        callback(step, total_steps, "1: Validating inputs...")
    if not channel_name and not channel_id:
        log("Cannot pull topics, no channel provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.1 Cannot pull topics, no channel provided...FAILED")
        return
    if channel_name and not channel_id:
        q_str = f"SELECT id, ch_id, ch_name FROM channel WHERE ch_name='{channel_name}';"
        stmt = or_(TelegramChannel.ch_name == channel_name)
        channel = await dbh.query_with_filter(TelegramChannel, stmt)
        if not channel:
            log("Cannot pull topics, channel not found in database.", level="ERROR")
            if callback:
                callback(step, total_steps, "1.2 Cannot pull topics, channel not found in database...FAILED")
            return
        if len(channel) > 1:
            log("Cannot pull topics using channel_name, multiple channels found in database.", level="ERROR")
            return

    if channel_id and not channel_name:
        stmt = or_(TelegramChannel.ch_id == channel_id)
        channel = await dbh.query_with_filter(TelegramChannel, stmt)
        if not channel:
            log("Cannot pull topics, channel not found in database.", level="ERROR")
            if callback:
                callback(step, total_steps, "1.2 Cannot pull topics, channel not found in database...FAILED")
            return
        if len(channel) > 1:
            log("Cannot pull topics using channel_id, multiple channels found in database.", level="ERROR")
            return
    db_ch_id = channel[0].id
    ch_name = channel[0].ch_name
    ch_id = channel[0].ch_id
    if not tg_a:
        log("Cannot pull topics, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.4 Cannot pull topics, no TGAccount provided...FAILED")
        return
    step += 1
    if callback:
        callback(step, total_steps, "2: Pulling topics from Telegram...")
    log("Pulling topics...", level="INFO")
    entity = await tg_a.get_peer(ch_name)
    topics = await tg_a.get_topics(channel_name=entity)
    log(f"Found {len(topics)} topics.", level="INFO")
    step += 1
    t_step = 1
    for topic in topics:
        if callback:
            callback(step, total_steps, f"3: Inserting topic {t_step}/{len(topics)} into database...")
        t = topics[topic]
        x = {
            'topic_name': t['title'],
            'topic_id': t['id'],
            'date_added': datetime.now(),
            'tg_ch_id': db_ch_id
        }
        topic = Topic(**x)
        await dbh.add_record(topic)
        t_step += 1


async def pull_messages(tg_a: TGAccount,
                        dbh: DBHelper,
                        channel_name: str = None,
                        channel_id: int = None,
                        callback=None,
                        offset_date: str = None,
                        offset_id: int = None,
                        filter_media=None):
    """
    Pull all messages from users Telegram and add them to the database.
    Args:
        tg_a:
        dbh:
        channel_name:
        channel_id:
        callback:
        filter_date:
        filter_media: ['image', 'video', 'document', 'music', 'voice', 'url']

    Returns:

    """
    filter = {
        'image': TGAccount.FILTER_PHOTO,
        'video': TGAccount.FILTER_VIDEO,
        'document': TGAccount.FILTER_DOCUMENT,
        'music': TGAccount.FILTER_MUSIC,
        'voice': TGAccount.FILTER_VOICE,
        'url': TGAccount.FILTER_URL
    }
    try:
        filter_media = filter[filter_media]
    except KeyError:
        log(f"Invalid filter_media: {filter_media}", level="ERROR")
        return
    total_steps = 3
    step = 1
    if callback:
        callback(step, total_steps, "1: Validating inputs...")
    if not channel_name and not channel_id:
        log("Cannot pull messages, no channel provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.1 Cannot pull messages, no channel provided...FAILED")
        return

    if not tg_a:
        log("Cannot pull messages, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.4 Cannot pull messages, no TGAccount provided...FAILED")
        return
    step += 1
    if callback:
        callback(step, total_steps, "2: Pulling messages from Telegram...")
    log("Pulling messages...", level="INFO")

    entity = await tg_a.get_peer(channel_name)
    # try and get the last time the channel was updated
    q_str = f"SELECT id FROM channel WHERE ch_id = {entity.id};"
    db_channel_id = dbh.execute_db_command(q_str)[0][0]
    q_str = f"SELECT MAX(msg_id) AS max_msg_id FROM message WHERE tg_ch_id = {db_channel_id};"
    last_msg_id = dbh.execute_db_command(q_str)
    if last_msg_id[0][0]:
        last_msg_id = last_msg_id[0][0] + 1
    else:
        last_msg_id = 0
    messages = await tg_a.get_messages(entity=entity,
                                       msg_filter=filter_media,
                                       callback=callback,
                                       min_id=last_msg_id,
                                       limit=None)
    if not messages:
        log(f"No messages found or no new messages since message: {last_msg_id - 1}.", level="INFO")
        if callback:
            callback(step, total_steps, f"2.1 No new messages found since message: {last_msg_id - 1}...")
        return
    step += 1
    m_step = 1

    # TODO - update the last updated date for the channel. Also implement
    # pulling the videos based on the last updated date.
    date_ch_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_msg = len(messages)
    for m in messages:
        try:
            if m.reply_to_msg_id:
                q_str = f"SELECT id FROM topic WHERE topic_id={m.reply_to_msg_id};"
                topic_id = dbh.execute_db_command(q_str)[0][0]
        except Exception as e:
            log(f"Error getting topic ID for message {m.id}: {e}", level="ERROR")
            topic_id = None
        try:
            q_str = f"SELECT id FROM channel WHERE ch_id={m.peer_id.channel_id};"
            channel_id = dbh.execute_db_command(q_str)[0][0]
        except Exception as e:
            log(f"Error getting channel ID for message {m.id}: {e}", level="ERROR")
            channel_id = None
        try:
            thumb = base64.b64encode(m.media.document.thumbs.bytes).decode('utf-8') if m.media.document else None
        except Exception as e:
            thumb = None
        try:
            x = {
                'name': m.message,
                'msg_id': m.id,
                'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S%z"),
                'date_posted': m.date
                'tg_ch_id': channel_id,
                'topic_id': topic_id
            }
            dbh.insert_into_table(Message, filter_column='msg_id', filter_value=x['msg_id'], **x)
            if callback:
                callback(m_step, total_msg, f"3: Inserting message {m_step}/{total_msg} into database...")
            m_step += 1
        except Exception as e:
            log(f"Error inserting message {m.id}: {e}", level="ERROR")
    dbh.update_channel_last_time(datetime.now().strftime("%Y-%m-%d %H:%M:%S%z"), entity.id)


async def pull_videos(tg_a: TGAccount,
                      db_url: str,
                      channel_name: str = None,
                      channel_id: int = None,
                      callback=None):
    """
    Pull all videos from users Telegram and add them to the database.
    :param tg_a:
    :param db_url:
    :param channel_name:
    :param channel_id:
    :param callback: An optional callback function to update the progress.
    :return:
    """
    total_steps = 3
    step = 1
    dbh = DBHelper(db_url)
    # Step 1: Validate the inputs
    if callback:
        callback(step, total_steps, f"1.1: Validating inputs...")
    if not channel_name and not channel_id:
        log("Cannot pull videos, no channel provided.", level="ERROR")
        if callback:
            callback(step, total_steps, f"1.2: Cannot pull videos, no channel provided....FAILED")
        return
    if channel_name and not channel_id:
        q_str = f"SELECT id, ch_id, channel_name FROM tg_channel WHERE channel_name='{channel_name}';"
        channel = await dbh.execute_db_command(q_str)
        if not channel:
            log("Cannot pull videos, channel not found in database.", level="ERROR")
            if callback:
                callback(step, total_steps, f"1.3: Cannot pull videos, channel not found in database...FAILED")
            return
        if len(channel) > 1:
            log("Cannot pull videos using channel_name, multiple channels found in database.", level="ERROR")
        db_channel_id = channel[0][0]
        channel_id = channel[0][1]
        channel_name = channel[0][2]
    if channel_id and not channel_name:
        q_str = f"SELECT id, channel_name FROM tg_channel WHERE ch_id={channel_id};"
        channel = await dbh.execute_db_command(q_str)
        if not channel:
            log("Cannot pull videos, channel not found in database.", level="ERROR")
            if callback:
                callback(step, total_steps, f"1.4: Cannot pull videos, channel not found in database...FAILED")
            return
        if len(channel) > 1:
            log("Cannot pull videos using channel_id, multiple channels found in database.", level="ERROR")
        db_channel_id = channel[0][0]
        channel_name = channel[0][1]
    if not db_url:
        log("Cannot pull videos, no database URL provided.", level="ERROR")
        if callback:
            callback(step, total_steps, f"1.5: Cannot pull videos, no database URL provided...FAILED")
        return
    if not tg_a:
        log("Cannot pull videos, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, f"1.6: Cannot pull videos, no TGAccount provided...FAILED")
        return
    step += 1
    if callback:
        callback(step, total_steps, f"2: Pulling topics from database...")
    q_str = f"SELECT id, topic_id FROM tg_topic WHERE telegram_channel_id={db_channel_id};"
    db_topics = await dbh.execute_db_command(q_str)
    if not db_topics:
        log("No topics found in database.", level="ERROR")
        if callback:
            callback(step, total_steps, f"2.1: No topics found in database...FAILED")
        return
    topic_dict = {}
    for db_topic in db_topics:
        topic_dict[db_topic[1]] = db_topic[0]

    step += 1
    log("Pulling videos...", level="INFO")
    videos = await tg_a.get_media_message(channel_name, db_url, callback)
    # log(f"Found {len(videos)} videos.", level="INFO")
    # vid_num = 0
    # for video in videos:
    #     vid_num += 1
    #     if callback:
    #         callback(step, total_steps, f"3: Inserting video {vid_num}/{len(videos)} into database...")
    #     v = videos[video]
    #     try:
    #         t_id = topic_dict[v['topic_id']]
    #     except KeyError:
    #         t_id = None
    #         log("KeyError: 'topic_id' not found in video.", level="ERROR")
    #
    #     x = {
    #         'name': v['title'],
    #         'msg_id': v['id'],
    #         'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #         'date_posted': v['date_posted'],
    #         'raw_obj': v['raw_obj'].stringify(),
    #         'telegram_channel_id': db_channel_id,
    #         'topic_id': t_id,
    #         'thumb': v['thumb']
    #     }
    #     insert_into_table(db_url, Message, filter_column='msg_id', filter_value=x['msg_id'], **x)


pool = pool.SimpleConnectionPool(
    host='127.0.0.1',
    user='user',
    password='password',
    database='moviesdb',
    minconn=1,
    maxconn=10,
    connect_timeout=10
)


def insert_tag(tag):
    try:
        connection = pool.getconn()
        cursor = connection.cursor()
        x = {'tag_name': tag}
        cursor.execute("INSERT INTO tg_tag (tag_name) VALUES (%(tag_name)s)", x)
        connection.commit()
    except IntegrityError:
        pass
    except Exception as e:
        log(f"Error inserting tag {tag}: {e}", level="ERROR")
    finally:
        cursor.close()
        connection.close()


def get_tag_id(tag):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM tg_tag WHERE tag_name = %s", (tag,))
        result = cursor.fetchone()
        return result[0] if result else None
    except IntegrityError:
        pass
    except Exception as e:
        log(f"Error getting tag ID for {tag}: {e}", level="ERROR")
        return None
    finally:
        cursor.close()
        connection.close()


def insert_message_tag(msg_id, tag_id):
    try:
        connection = pool.get_connection()
        cursor = connection.cursor()
        y = {'message_id': msg_id, 'tag_id': tag_id}
        cursor.execute("INSERT INTO tg_message_tag (message_id, tag_id) VALUES (%(message_id)s, %(tag_id)s)", y)
        connection.commit()
    except IntegrityError:
        pass
    except Exception as e:
        log(f"Error inserting message tag {msg_id} - {tag_id}: {e}", level="ERROR")
    finally:
        cursor.close()
        connection.close()


async def process_tags_for_message(db_url, message_dict, msg_id, callback, step, total_steps, msg_id_step):
    tags = message_dict[msg_id]['tags']
    if callback:
        callback(step, total_steps, f"4: Inserting tags for message "
                                    f"{msg_id_step}/{len(message_dict)} -- "
                                    f"{len(tags)} total tags for current message...")
    for tag in tags:
        insert_tag(tag)
        try:
            # Sanitize the tag to prevent SQL injection
            sanitized_tag = tag.replace("'", "").replace('"', "")
            tag_id = get_tag_id(sanitized_tag)
            if tag_id is not None:
                insert_message_tag(msg_id, tag_id)
        except Exception as e:
            log(f"Error processing tag {tag} for message {msg_id}: {e}", level="ERROR")


async def create_tags(tg_a: TGAccount,
                      db_url: str,
                      callback=None):
    """
    Create tags for all messages in the database.
    :param tg_a:
    :param db_url:
    :param callback:
    :return:
    """
    total_steps = 4
    step = 1
    if callback:
        callback(step, total_steps, "1: Validating inputs...")
    if not db_url:
        log("Cannot create tags, no database URL provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.1 Cannot create tags, no database URL provided...FAILED")
        return
    if not tg_a:
        log("Cannot create tags, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.2 Cannot create tags, no TGAccount provided...FAILED")
        return
    step += 1
    if callback:
        callback(step, total_steps, "2: Pulling messages from database to create tags...")
    log("Creating tags...", level="INFO")
    q_str = "SELECT id, name FROM tg_message;"
    db_messages = execute_db_command(db_url, q_str)
    if not db_messages:
        log("No messages found in database.", level="ERROR")
        if callback:
            callback(step, total_steps, "2.1 No messages found in database...FAILED")
        return
    step += 1
    message_dict = {}
    db_msg_step = 1
    for db_message in db_messages:
        if callback:
            callback(step, total_steps, f"3: Creating tags for message {db_msg_step}/{len(db_messages)}...")
        message_dict[db_message[0]] = {
            'name': db_message[1],
            'tags': generate_tags(db_message[1])
        }
        db_msg_step += 1
    step += 1
    msg_id_step = 1
    tasks = []
    for msg_id in message_dict:
        tasks.append(process_tags_for_message(db_url, message_dict, msg_id, callback, step, total_steps, msg_id_step))
        msg_id_step += 1

    # Await completion of all tasks
    await asyncio.gather(*tasks)

    # for msg_id in message_dict:
    #     tags = message_dict[msg_id]['tags']
    #     if callback:
    #         callback(step, total_steps, f"4: Inserting tags for message "
    #                                     f"{msg_id_step}/{len(message_dict)} -- "
    #                                     f"{len(tags)} total tags for current message...")
    #     for tag in tags:
    #         x = {'tag_name': tag}
    #         insert_into_table(db_url, Tags, filter_column=None, filter_value=None, **x)
    #         try:
    #             tag = tag.replace("'", "").replace('"', "")
    #             tag_id = execute_db_command(db_url, f"SELECT id FROM tg_tag WHERE tag_name='{tag}';")[0][0]
    #             y = {
    #                 'message_id': msg_id,
    #                 'tag_id': tag_id
    #             }
    #             insert_into_table(db_url, MessageTags, filter_column=None, filter_value=None, **y)
    #         except TypeError:
    #             continue
    #         except IndexError:
    #             continue
    #     msg_id_step += 1


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
