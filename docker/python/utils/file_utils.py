import os
import datetime


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

