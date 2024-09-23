from .db_utils import DBHelper, MonitoredItem, Topic, TelegramChannel, DLFolder
from .log_utils import log
import streamlit as st
import asyncio
import os

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

async def do_add_monitored(name, db_url, root_file_path='/monitored'):
    db = DBHelper(db_url)
    topic_id = await db.query_with_filter(Topic,
                                          Topic.topic_name ==
                                          name)
    if not topic_id:
        log(f"Topic {name} not found in db, not adding to monitored list", 'warning')
        return
    await db.add_record(MonitoredItem(topic_id=topic_id[0].id,
                                      is_monitored=True))
    log(f"Added '{name}' to monitored list in db", 'success')
    path = create_monitored_folder(name)
    if path:
        await db.add_record(DLFolder(topic_id=topic_id[0].id,
                                     folder_path=path,
                                     ch_id=topic_id[0].tg_ch_id))
        log(f"Added '{path}' to monitored folder in db", 'success')
        st.success(f"Added '{name}' to monitored list. Downloaded files can "
                   f"be found in the ':red[{path}]' folder",
                   icon=":material/thumb_up:")

async def do_remove_monitored(name, db_url):
    db = DBHelper(db_url)
    topic_id = await db.query_with_filter(Topic,
                                          Topic.topic_name ==
                                          name)
    if not topic_id:
        log(f"Topic {name} not found in db, not removing from monitored list", 'warning')
        return
    print(topic_id)
    filter_cond = MonitoredItem.topic_id == topic_id[0].id
    await db.delete_record(MonitoredItem, filter_cond)
    log(f"Removed '{name}' from monitored list in db", 'success')
    filter_cond = DLFolder.topic_id == topic_id[0].id
    await db.delete_record(DLFolder,
                           DLFolder.topic_id == topic_id[0].id)
    log(f"Removed '{name}' from monitored folder in db", 'success')
    st.success(f"Removed '{name}' from monitored list",
               icon=":material/thumb_up:")


def create_monitored_folder(name, root_file_path='/monitored'):
    # Create a folder in the root file path if it doesn't exist
    name = name.replace(' ', '_').lower()
    folder_path = f"{root_file_path}/{name}"
    try:
        os.makedirs(folder_path) if not os.path.exists(folder_path) else None
        return folder_path
    except OSError:
        print(f"Creation of the directory {folder_path} failed")
        return None

def add_monitored(name, db_url, root_file_path='/monitored'):
    asyncio.run(do_add_monitored(name, db_url, root_file_path))

def remove_monitored(name, db_url):
    asyncio.run(do_remove_monitored(name, db_url))

def is_monitored(name, db_url):
    return asyncio.run(do_is_monitored(name, db_url))