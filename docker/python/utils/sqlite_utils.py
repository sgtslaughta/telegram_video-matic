import sqlite3
from .log_utils import log


def create_database(database_name: str):
    """
    Create a SQLite database with 3 tables: videos, telegram_channel, and dl_folder.
    :param database_name: str
    :return:
    """
    try:
        conn = sqlite3.connect(database_name)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        cursor = conn.cursor()

        # Create videos table with additional columns and foreign key constraints
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                name TEXT,
                size INTEGER,
                date_added TEXT,
                full_path TEXT,
                tags TEXT,
                dl_folder_id INTEGER,
                telegram_channel_id INTEGER,
                FOREIGN KEY (dl_folder_id) REFERENCES dl_folder(id),
                FOREIGN KEY (telegram_channel_id) REFERENCES telegram_channel(id)
            )
        ''')

        # Create telegram_channel table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_channel (
                id INTEGER PRIMARY KEY,
                channel_name TEXT,
                description TEXT,
                date_created TEXT
            )
        ''')

        # Create dl_folder table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dl_folder (
                id INTEGER PRIMARY KEY,
                folder_path TEXT,
                date_added TEXT
            )
        ''')

        conn.commit()
        log(msg="SQLite database connected successfully.",
            level="SUCCESS")
        conn.close()
    except sqlite3.Error as e:
        log(msg=f"Error connecting to SQLite database: {e}",
            level="ERROR")

