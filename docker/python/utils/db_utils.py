# from scripts.run_emscripten_tests import driver
# from utils.log_utils import log
# from docker.python.message_test import db_url
from datetime import datetime as dt
from os import environ

# from utils.tg_utils import catch_and_log_errors
from sqlalchemy import (Column, Integer, String, ForeignKey,
                        Text, DateTime, Boolean, Sequence, event, func, delete)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from utils.log_utils import log

Base = declarative_base()


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String(255), nullable=False)
    msg_id = Column(Integer, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), nullable=False, default=func.now())
    date_posted = Column(DateTime(timezone=True), nullable=False)
    is_media = Column(Boolean, nullable=False)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topic.id'))

    def __repr__(self):
        return (f"<Message(id={self.id}, name={self.name}, msg_id"
                f"={self.msg_id}, date_added={self.date_added}, "
                f"date_posted={self.date_posted}, is_media={self.is_media}, tg_ch_"
                f"id={self.tg_ch_id}, topic_id"
                f"={self.topic_id})>")


class ServerTasks(Base):
    __tablename__ = 'svr_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    func_name = Column(String(255), nullable=False)
    args = Column(Text)
    interval_s = Column(Integer, nullable=False)
    next_run_time = Column(DateTime(timezone=True), nullable=False)
    is_complete = Column(Boolean, nullable=False)
    is_oneshot = Column(Boolean, nullable=False)

    def __repr__(self):
        return (f"<ServerTasks(id={self.id}, func_name={self.func_name}, args"
                f"={self.args}, interval_s={self.interval_s}, next_run_time"
                f"={self.next_run_time}, is_complete={self.is_complete},"
                f"is_oneshot={self.is_oneshot})>")

class MonitoredItem(Base):
    __tablename__ = 'monitored_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topic.id'), primary_key=True,
                      unique=True)
    date_added = Column(DateTime(timezone=True), default=func.now())
    date_last_updated = Column(DateTime(timezone=True), default=func.now())
    is_monitored = Column(Boolean, nullable=False)

    def __repr__(self):
        return (f"<MonitoredChannel(ch_id={self.topic_id}, date_added"
                f"={self.date_added}, date_last_updated"
                f"={self.date_last_updated}, is_active={self.is_monitored})>")

@event.listens_for(MonitoredItem, 'before_update')
def receive_before_update(mapper, connection, target):
    target.date_last_updated = dt.now()


class TelegramChannel(Base):
    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ch_name = Column(String(255))
    ch_id = Column(Integer, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), default=func.now())
    date_last_updated = Column(DateTime(timezone=True), default=func.now(),
                               onupdate=func.now())
    last_msg_id = Column(Integer, ForeignKey('message.id'))

    def __repr__(self):
        return (f"<TelegramChannel(id={self.id}, ch_name={self.ch_name}, "
                f"ch_id={self.ch_id}, date_added"
                f"={self.date_added}, date_last_updated"
                f"={self.date_last_updated}, last_msg_id={self.last_msg_id})>")

@event.listens_for(TelegramChannel, 'before_update')
def receive_before_update(mapper, connection, target):
    target.date_last_updated = dt.now()

class Topic(Base):
    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255), unique=True)
    topic_id = Column(Integer, unique=True)
    date_added = Column(DateTime(timezone=True), default=func.now())
    tg_ch_id = Column(Integer, ForeignKey('channel.id'))

    def __repr__(self):
        return (f"<Topic(id={self.id}, topic_name={self.topic_name}, "
                f"topic_id={self.topic_id}, date_added={self.date_added}, "
                f"tg_ch_id={self.tg_ch_id})>")


class DLFolder(Base):
    __tablename__ = 'dl_folder'

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), default=func.now())
    topic_id = Column(Integer, ForeignKey('topic.id'))
    ch_id = Column(Integer, ForeignKey('channel.id'))

    def __repr__(self):
        return (f"<DLFolder(id={self.id}, folder_path={self.folder_path}, "
                f"date_added={self.date_added}, topic_id={self.topic_id},"
                f"ch_id={self.ch_id})>")


class DLFile(Base):
    __tablename__ = 'dl_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    msg_id = Column(Integer, unique=True, nullable=False)
    date_added = Column(DateTime(timezone=True), default=func.now())
    path = Column(Text, nullable=False, unique=True)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'))
    topic_id = Column(Integer, ForeignKey('topic.id'))

    def __repr__(self):
        return (f"<DLFile(id={self.id}, name={self.name}, msg_id"
                f"={self.msg_id}, "
                f"date_added={self.date_added}, path={self.path}, tg_ch_id"
                f"={self.tg_ch_id}, topic_id={self.topic_id})>")


class Tags(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(255), unique=True)

    def __repr__(self):
        return f"<Tags(id={self.id}, tag_name={self.tag_name})>"


class MessageTags(Base):
    __tablename__ = 'message_tag'

    message_id = Column(Integer, ForeignKey('message.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)

class FolderTags(Base):
    __tablename__ = 'folder_tag'

    folder_id = Column(Integer, ForeignKey('dl_folder.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)

class FileTags(Base):
    __tablename__ = 'file_tag'

    file_id = Column(Integer, ForeignKey('dl_file.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'), primary_key=True)

class ServerSettings(Base):
    __tablename__ = 'svr_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_name = Column(String(255), unique=True)
    setting_value = Column(Text)

    def __repr__(self):
        return (f"<ServerSettings(id={self.id}, setting_name={self.setting_name}, "
                f"setting_value={self.setting_value})>")


class DBHelper:
    def __init__(self, database_url: str,
                 pool_size: int = 15,
                 max_overflow: int = 32):
        self.db_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine = create_async_engine(database_url, poolclass=NullPool)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def drop_table(self, table):
        async with self.engine.begin() as conn:
            await conn.run_sync(table.__table__.drop)

    async def clear_table(self, table):
        async with self.engine.begin() as conn:
            stmt = delete(table)
            await conn.execute(stmt)

    async def add_record(self, new_record):
        try:
            async with self.async_session() as session:
                async with session.begin():
                    session.add(new_record)
                    await session.commit()
        except IntegrityError as e:
            log(f"Duplicate record attempt, ignored...", level="INFO")

    async def get_record(self, table, record_id: int):
        async with self.async_session() as session:
            result = await session.execute(
                select(table).filter(table.id == record_id))
            record = result.scalars().first()
            return record

    async def update_record(self, table, new_record, filter_condition=None):
        """
        Update a record in the database based on the filter_condition.
        If a record with the same id exists, update it with the values from new_record.
        """
        async with self.async_session() as session:
            async with session.begin():
                # Fetch the existing record
                result = await session.execute(
                    select(table).filter(filter_condition))
                existing_record = result.scalars().first()

                # Check if the record exists
                if existing_record:
                    # Update the existing record with values from new_record
                    for attr, value in vars(new_record).items():
                        if hasattr(existing_record,
                                   attr) and attr != 'id':  # Ignore updating the 'id'
                            setattr(existing_record, attr, value)
                    # Commit the changes
                    await session.commit()
                    return existing_record
                else:
                    # Handle case where no record is found
                    return None

    async def delete_record(self, table, filter_condition=None):
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(table).filter(filter_condition))
                record = result.scalars().first()
                if record:
                    await session.delete(record)
                    await session.commit()

    async def list_records(self, table) -> Sequence[DeclarativeMeta]:
        async with self.async_session() as session:
            result = await session.execute(select(table))
            records = result.scalars().all()
            return records

    async def query_with_filter(self, table, filter_condition) -> Sequence[
        DeclarativeMeta]:
        """
        Query the table with a filter condition.

        :param filter_condition: A SQLAlchemy filter condition (e.g., MyModel.name == 'some_name')
        :return: A list of records matching the filter condition
        """
        async with self.async_session() as session:
            stmt = select(table).filter(filter_condition)
            result = await session.execute(stmt)
            records = result.scalars().all()
            return records




def init_db():
    """
    Initialize the database connection and create the tables.

    Returns:

    """
    if 'DB_NAME' not in environ:
        log("DB_NAME required, quitting.", level="ERROR")
        exit(1)
    if 'DB_USER' not in environ:
        log("REQUIRED: DB_USER environment variable not set, quitting.",
            level="ERROR")
        exit(1)
    user = environ['DB_USER']
    if 'DB_PASSWORD' not in environ:
        log("REQUIRED: DB_PASSWORD environment variable not set, "
            "quitting.", level="ERROR")
        exit(1)
    password = environ['DB_PASSWORD']
    if 'DB_HOST' not in environ:
        log("REQUIRED: DB_HOST environment variable not set, "
            "using localhost.", level="ERROR")
        host = 'localhost'
    else:
        host = environ['MYSQL_HOST']
    if 'DB_PORT' not in environ:
        log("DB_PORT environment variable not set, using 3306.",
            level="ERROR")
        port = 5432
    else:
        port = environ['DB_PORT']
    if 'DB_DATABASE' not in environ:
        log("REQUIRED: DB_DATABASE environment variable not set, "
            "quitting.", level="ERROR")
        exit(1)
    db = environ['DB_NAME']
    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    dbh = DBHelper(database_url)
    dbh.create_tables()
    environ['DB_URL'] = database_url
