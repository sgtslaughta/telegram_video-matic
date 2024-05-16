from .db_utils import insert_into_table, TelegramChannel, Topic
from .db_utils import execute_db_command
from .db_utils import Message, MessageTags, DLFolder, Tags
from .tg_utils import TGAccount
from .log_utils import log
from .tag_utils import generate_tags
import asyncio
from datetime import datetime
import mysql.connector
from mysql.connector import pooling
from mysql.connector.errors import IntegrityError


async def pull_channels(tg_a: TGAccount, db_url: str, callback=None):
    """
    Pull all channels from users Telegram and add them to the database.
    :param tg_a: TGAccount
    :param db_url: str
    :param callback: An optional callback function to update the progress.
    :return:
    """
    total_steps = 3
    step = 1
    if callback:
        callback(step, total_steps, "1: Validating inputs...")
    if not db_url:
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
    log(f"Found {len(channels)} channels.", level="INFO")
    step += 1
    ch_step = 1
    for channel in channels:
        if callback:
            callback(step, total_steps, f"3: Inserting channel {ch_step}/{len(channels)} into database...")
        ch = channels[channel]
        x = {
            'channel_name': ch['name'],
            'ch_id': ch['id'],
            'raw_obj': ch['raw_obj'].stringify(),
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'date_last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        insert_into_table(db_url, TelegramChannel, filter_column='ch_id', filter_value=x['ch_id'], **x)
        ch_step += 1


async def pull_topics(tg_a: TGAccount,
                      db_url: str,
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
        q_str = f"SELECT id, ch_id, channel_name FROM tg_channel WHERE channel_name='{channel_name}';"
        channel = execute_db_command(db_url, q_str)
        if not channel:
            log("Cannot pull topics, channel not found in database.", level="ERROR")
            if callback:
                callback(step, total_steps, "1.2 Cannot pull topics, channel not found in database...FAILED")
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
            if callback:
                callback(step, total_steps, "1.2 Cannot pull topics, channel not found in database...FAILED")
            return
        if len(channel) > 1:
            log("Cannot pull topics using channel_id, multiple channels found in database.", level="ERROR")
        db_ch_id = channel[0][0]
        ch_name = channel[0][1]
        ch_id = channel_id
    if not db_url:
        log("Cannot pull topics, no database URL provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.3 Cannot pull topics, no database URL provided...FAILED")
        return
    if not tg_a:
        log("Cannot pull topics, no TGAccount provided.", level="ERROR")
        if callback:
            callback(step, total_steps, "1.4 Cannot pull topics, no TGAccount provided...FAILED")
        return
    step += 1
    if callback:
        callback(step, total_steps, "2: Pulling topics from Telegram...")
    log("Pulling topics...", level="INFO")
    topics = await tg_a.get_topics(channel_name=ch_id)
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
            'raw_obj': t['raw_obj'].stringify(),
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'telegram_channel_id': db_ch_id
        }
        insert_into_table(db_url, Topic, filter_column='topic_id', filter_value=x['topic_id'], **x)
        t_step += 1


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
        channel = execute_db_command(db_url, q_str)
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
        channel = execute_db_command(db_url, q_str)
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
    db_topics = execute_db_command(db_url, q_str)
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
    videos = await tg_a.get_all_videos(channel_name, db_url, callback)
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

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=25,
    pool_reset_session=True,
    host='127.0.0.1',
    user='user',
    password='password',
    database='moviesdb'
)


def insert_tag(tag):
    try:
        connection = pool.get_connection()
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


# url = "mysql+mysqlconnector://user:password@127.0.0.1:3306/moviesdb"
# tg = TGAccount(26748451, '00200de1624adc3900bfc3075665dd40')
# asyncio.run(run_all(tg, url, 'Rugby Try-Lights'))
