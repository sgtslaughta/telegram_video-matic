from .db_utils import DBHelper, DLFolder, Topic, TelegramChannel, Message
from .tg_utils import TGAccount
from .log_utils import log
import os
import datetime
import re
import asyncio


def format_file_name(file_name: str, date_time: datetime.datetime = None, msg_id: int = None):
    # DD-MM-YYYY
    date = date_time.strftime('%d-%m-%Y')
    file_name = file_name.replace('_', ' ')
    file_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', file_name)
    file_name = file_name.replace(' v ', ' vs ')
    file_name = f"{msg_id}: {file_name} - {date}"
    return file_name


def determine_season(date):
    # Get the current year
    current_year = date.year

    # Check if the date is prior to August of the current year
    if date < datetime.datetime(current_year, 8, 1):
        prior_year = current_year - 1
        return f"{prior_year}-{current_year}"
    else:
        next_year = current_year + 1
        return f"{current_year}-{next_year}"


def get_video_details(file_path):
    return {
        "f_name": os.path.basename(file_path),
        "f_sz_b": os.path.getsize(file_path),
        "c_time": datetime.datetime.fromtimestamp(
            os.path.getctime(file_path)),
        "m_time": datetime.datetime.fromtimestamp(
            os.path.getmtime(file_path)),
        "a_time": datetime.datetime.fromtimestamp(
            os.path.getatime(file_path)),
        "f_path": file_path
    }


def scan_video_directory(directory):
    video_details = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
                file_path = os.path.join(root, file)
                try:
                    details = get_video_details(file_path)
                    video_details[file] = details
                except Exception as e:
                    print(f"Error processing file: {file_path} - {e}")
    return video_details


async def search_missing_files(db, topic_id):
    topic_msgs = await db.query_with_filter(Message, Message.topic_id == topic_id)
    path = await db.query_with_filter(DLFolder, DLFolder.topic_id == topic_id)
    if not path:
        log(f"Folder for topic {topic_id} not found", 'error')
        return []
    path = path[0].folder_path
    topic_msgs_ids = [msg.msg_id for msg in topic_msgs]
    files_in_folder = scan_video_directory(path)
    files_by_id_list = [f.split(':')[0] for f in files_in_folder.keys()]
    return [msg for msg in topic_msgs if msg.msg_id not in files_by_id_list], path


async def compare_missing_files(db, tga, topic_id, concurrent_amt=5):
    missing_files, root_path = await search_missing_files(db, topic_id)
    if not missing_files:
        log(f"No missing files found for topic {topic_id}", 'info')
        return
    msg_obj_list = []
    ch = await db.query_with_filter(TelegramChannel, TelegramChannel.id == missing_files[0].tg_ch_id)
    ch_name = ch[0].ch_name
    msg_dict_list = []
    msg_obj_list = await tga.get_messages_by_id([msg.msg_id for msg in missing_files], ch_name)
    for msg in msg_obj_list.messages:
        msg_dict_list.append({
            'msg_obj': msg,
            'file_name': format_file_name(msg.message[:255], msg.date, msg.id),
            'path': f"{root_path}/{msg.date.year}"
        })
    return msg_dict_list


async def s_and_d(tgh, db, topic_id, concurrent_amt=5):
    files = await compare_missing_files(db, tgh, topic_id, concurrent_amt)
    await tgh.multi_download(files, concurrent_amt=concurrent_amt)


def search_missing_and_dl(tgh, db, topic_id, concurrent_amt=5):
    files = asyncio.run(s_and_d(tgh, db, topic_id, concurrent_amt))

