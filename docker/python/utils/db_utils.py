from utils.log_utils import log
from utils.tg_utils import catch_and_log_errors
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from os import environ
from functools import wraps

Base = declarative_base()


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    msg_id = Column(Integer, unique=True)
    date_added = Column(Date)
    date_posted = Column(Date)
    raw_obj = Column(Text)
    thumb = Column(Text)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'))
    topic_id = Column(Integer, ForeignKey('topic.id'))


class TelegramChannel(Base):
    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ch_name = Column(String(255))
    ch_id = Column(Integer, unique=True)
    raw_obj = Column(Text)
    date_added = Column(Date)
    date_last_updated = Column(Date)
    last_msg_id = Column(Integer, ForeignKey('message.id'))


class Topic(Base):
    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255))
    topic_id = Column(Integer)
    date_added = Column(Date)
    raw_obj = Column(Text)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'))


class DLFolder(Base):
    __tablename__ = 'dl_folder'

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text)
    date_added = Column(Date)
    tags = Column(Text)


class Tags(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(255), unique=True)


class MessageTags(Base):
    __tablename__ = 'message_tag'

    message_id = Column(Integer, ForeignKey('message.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)


class DBHelper:
    def __init__(self, database_url: str,
                 pool_size: int = 15,
                 max_overflow: int = 25):
        self.db_url = None
        self.pool_size = None
        self.max_overflow = None
        self.engine = None
        self.new_session = None
        self._initialize(database_url, pool_size, max_overflow)

    def _initialize(self, database_url: str, pool_size: int, max_overflow: int):
        if not database_url:
            log("Database URL not provided.", level="ERROR")
            return

        try:
            self.db_url = database_url
            self.pool_size = pool_size
            self.max_overflow = max_overflow
            self.engine = create_engine(database_url,
                                        pool_size=pool_size,
                                        max_overflow=max_overflow)
            self.new_session = sessionmaker(bind=self.engine)
            self.create_database()
        except Exception as e:
            log(f"Error initializing database: {e}", level="ERROR")

    def create_database(self):
        """
        Create a database with 6 tables: videos, telegram_channel, and dl_folder,
        topic, tags, and message_tags. The db will work with sqlite and mysql.

        \n## Example usage ## \n
        database_url = 'mysql+mysqlconnector://your_username:your_password@localhost:3306/your_database_name' \n
        create_database(database_url) \n
        :param database_url: str
        :return:
        """
        try:
            Base.metadata.create_all(self.engine)
            with self.new_session() as session:
                session.commit()
                log(f"Database '{self.engine.url.database}': connected successfully.", level="SUCCESS")
        except Exception as e:
            log(f"Error connecting to database: {e}", level="ERROR")

    @contextmanager
    async def new_async_session(self):
        async_session = self.new_session
        try:
            yield async_session()
        finally:
            async_session.close()

    @catch_and_log_errors
    async def execute_db_command(self, execute_str: str):
        """
        Execute a database command.
        :param execute_str:
        :return:
        """
        async with self.new_async_session() as session:
            result = await session.execute(text(execute_str))
            result = result.fetchall()
            return result

    @catch_and_log_errors
    async def insert_into_table(self, table_cls: DeclarativeMeta,
                                filter_column: str = None,
                                filter_value: str = None,
                                **kwargs):
        async with self.new_async_session() as session:
            if filter_column:
                existing_row = session.query(table_cls).filter(
                    getattr(table_cls, filter_column) == filter_value).first()
                if existing_row:
                    log(f"Row with {filter_column} '{filter_value}' already exists in table.", level="INFO")
                    return

            new_row = table_cls(**kwargs)
            session.add(new_row)
            session.commit()
            log(f"Data inserted into: '{table_cls.__tablename__}' successfully.", level="SUCCESS")

    @catch_and_log_errors
    async def modify_row(self,
                         table_cls: DeclarativeMeta,
                         primary_key_value: int,
                         **kwargs):
        async with self.new_async_session() as session:
            row_to_modify = session.query(table_cls).filter(table_cls.id == primary_key_value).first()
            for key, value in kwargs.items():
                setattr(row_to_modify, key, value)
            session.commit()
            log("Row modified successfully.", level="SUCCESS")

    @catch_and_log_errors
    async def map_msg_ids(self) -> dict:
        async with self.new_async_session() as session:
            table = Base.metadata.tables[Message]
            rows = session.query(table).all()
            id_map = {row.msg_id: row.id for row in rows}
            return id_map

    @catch_and_log_errors
    async def map_topic_ids(self) -> dict:
        try:
            async with self.new_async_session() as session:
                table = Base.metadata.tables['tg_topic']
                rows = session.query(table).all()
                id_map = {row.topic_id: row.id for row in rows}
                return id_map
        except Exception as e:
            log(f"Error mapping topic IDs: {e}", level="ERROR")
        finally:
            session.close()

    @catch_and_log_errors
    async def map_channel_ids(self) -> dict:
        async with self.new_async_session() as session:
            table = Base.metadata.tables['tg_channel']
            rows = session.query(table).all()
            id_map = {}
            for row in rows:
                id_map[row.ch_id] = row.id
            return id_map

    @catch_and_log_errors
    async def delete_rows(self, table_cls: type, where_clause: str):
        async with self.new_async_session() as session:
            delete_query = f"DELETE FROM {table_cls.__tablename__} WHERE {where_clause}"
            session.execute(text(delete_query))
            session.commit()
            log("Rows deleted successfully.", level="SUCCESS")


def init_db():
    """
    Initialize the database based on the environment variables
        MYSQL_USER,
        MYSQL_PASSWORD,
        MYSQL_HOST,
        MYSQL_PORT, and
        MYSQL_DATABASE.
    If the mysql environment variables are not set, the database will default to sqlite.
    Returns: None
    """
    if 'MYSQL_DATABASE' not in environ:
        log("MYSQL_DATABASE environment variable not set, using sqlite.", level="ERROR")
        database_url = 'sqlite:///../movie_db.sqlite'
    else:
        if 'MYSQL_USER' not in environ:
            log("REQUIRED: MYSQL_USER environment variable not set, quitting.", level="ERROR")
            exit(1)
        user = environ['MYSQL_USER']
        if 'MYSQL_PASSWORD' not in environ:
            log("REQUIRED: MYSQL_PASSWORD environment variable not set, quitting.", level="ERROR")
            exit(1)
        password = environ['MYSQL_PASSWORD']
        if 'MYSQL_HOST' not in environ:
            log("REQUIRED: MYSQL_HOST environment variable not set, using localhost.", level="ERROR")
            host = 'localhost'
        else:
            host = environ['MYSQL_HOST']
        if 'MYSQL_PORT' not in environ:
            log("MYSQL_PORT environment variable not set, using 3306.", level="ERROR")
            port = 3306
        else:
            port = environ['MYSQL_PORT']
        if 'MYSQL_DATABASE' not in environ:
            log("REQUIRED: MYSQL_DATABASE environment variable not set, quitting.", level="ERROR")
            exit(1)
        db = environ['MYSQL_DATABASE']
        database_url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}"
    dbh = DBHelper(database_url)
    dbh.create_database()
    environ['DATABASE_URL'] = database_url
