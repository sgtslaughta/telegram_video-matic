import asyncio
import os

import streamlit as st
from sqlalchemy import and_
from .db_utils import DBHelper, MonitoredItem, Topic, DLFolder, ServerTasks, TelegramChannel
from .log_utils import log
from .registered_funcs import scan_files, update_topic_msgs
from .svr_tasks import TaskQueue


async def do_is_monitored(item_name, db_url):
    db = DBHelper(db_url)
    item = await db.query_with_filter(Topic,
                                      Topic.topic_name ==
                                      item_name)
    if not item:
        return False
    channel = await db.query_with_filter(MonitoredItem,
                                         MonitoredItem.topic_id ==
                                         item[0].id)
    if not channel:
        return False
    return channel[0].is_monitored


async def _handle_monitored_folder(name, topic_id, db, root_file_path):
    path = create_monitored_folder(name)
    if path:
        await db.add_record(DLFolder(topic_id=topic_id.id,
                                     folder_path=path,
                                     ch_id=topic_id.tg_ch_id))
        log(f"Added '{path}' to monitored folder in db", 'success')
        st.success(f"Added '{name}' to monitored list. Downloaded files can "
                   f"be found in the ':red[{path}]' folder",
                   icon=":material/thumb_up:")
        return path
    else:
        msg = f"Failed to create folder for '{name}' in '{root_file_path}'"
        log(msg, 'error')
        st.error(msg)
        return None


async def _add_monitored_tasks(db, path, topic):
    # Add a task to scan the folder for new files
    # Check if the task already exists
    db_url = db.database_url
    filter_cond = and_(
        ServerTasks.args == path,
        ServerTasks.func_name == 'scan_files'
    )
    task = await db.query_with_filter(ServerTasks, filter_cond)
    if task:
        log(f"Task to scan '{path}' already exists", 'info')
        return
    else:
        task_queue = TaskQueue(db_url)
        await task_queue.add_task(scan_files, path, 300)

    log(f"Added task to scan '{path}' for new files", 'success')
    filter_cond = and_(
        ServerTasks.args == f"{topic.tg_ch_id}_{topic.id}",
        ServerTasks.func_name == 'update_topic_msgs'
    )
    task = await db.query_with_filter(ServerTasks, filter_cond)
    if task:
        log(f"Task to update topic messages already exists", 'info')
        return
    else:
        task_queue = TaskQueue(db_url)
        await task_queue.add_task(update_topic_msgs, f"{topic.tg_ch_id}_{topic.id}", 1800)
        log(f"Added task to update topic messages", 'success')
        await update_topic_msgs(f"{topic.tg_ch_id}_{topic.id}")
        log(f"Scanning for topic messages now", 'success')


async def do_add_monitored(name, db_url, root_file_path='/monitored'):
    db = DBHelper(db_url)
    topic = await db.query_with_filter(Topic,
                                          Topic.topic_name ==
                                          name)
    if not topic:
        log(f"Topic {name} not found in db, not adding to monitored list",
            'warning')
        return
    topic_id = topic[0].id
    topic_channel = await db.query_with_filter(TelegramChannel, TelegramChannel.id == topic[0].tg_ch_id)
    if not topic_channel:
        log(f"Channel {topic[0].tg_ch_id} not found in db, not adding to monitored list",
            'warning')
        return
    topic_ch_name = topic_channel[0].name
    path = await _handle_monitored_folder(name, topic[0], db, root_file_path)

    await db.add_record(MonitoredItem(topic_id=topic_id[0].id,
                                      is_monitored=True))
    log(f"Added '{name}' to monitored list in db", 'success')
    await _add_monitored_tasks(db, db_url, path)



async def do_remove_monitored(name, db_url):
    db = DBHelper(db_url)
    topic_id = await db.query_with_filter(Topic,
                                          Topic.topic_name ==
                                          name)
    if not topic_id:
        log(f"Topic {name} not found in db, not removing from monitored list",
            'warning')
        return
    filter_cond = MonitoredItem.topic_id == topic_id[0].id
    await db.delete_record(MonitoredItem, filter_cond)
    log(f"Removed '{name}' from monitored list in db", 'success')
    filter_cond = DLFolder.topic_id == topic_id[0].id
    folder = await db.query_with_filter(DLFolder, filter_cond)
    await db.delete_record(DLFolder,
                           DLFolder.topic_id == topic_id[0].id)
    log(f"Removed '{name}' from monitored folder in db", 'success')
    st.success(f"Removed '{name}' from monitored list",
               icon=":material/thumb_up:")
    # Remove the task to scan the folder for new files
    filter_cond = ServerTasks.args == folder[0].folder_path and \
                  ServerTasks.func_name == 'scan_files'
    task = await db.query_with_filter(ServerTasks, filter_cond)
    if task:
        svr_tasks = TaskQueue(db_url)
        await svr_tasks.remove_task(task[0].id)


def create_monitored_folder(name, root_file_path='/monitored'):
    # Create a folder in the root file path if it doesn't exist
    name = name.replace(' ', '_').lower()
    folder_path = f"{root_file_path}/{name}"
    try:
        os.makedirs(folder_path) if not os.path.exists(folder_path) else None
        return folder_path
    except OSError:
        st.error(f"Failed to create folder '{folder_path}'")
        return None


def add_monitored(name, db_url, root_file_path='/monitored'):
    asyncio.run(do_add_monitored(name, db_url, root_file_path))


def remove_monitored(name, db_url):
    asyncio.run(do_remove_monitored(name, db_url))


def is_monitored(name, db_url):
    return asyncio.run(do_is_monitored(name, db_url))


def get_videos(db_url):
    db = DBHelper(db_url)
    videos = db.list_records(MonitoredItem)
    return videos
