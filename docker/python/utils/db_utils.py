# from scripts.run_emscripten_tests import driver
# from utils.log_utils import log
# from docker.python.message_test import db_url
from utils.log_utils import log
import asyncio
from utils.tg_utils import catch_and_log_errors
# from utils.tg_utils import catch_and_log_errors
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, \
    create_async_pool_from_url
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text, Sequence
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import update
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from os import environ

Base = declarative_base()


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String(255), nullable=False)
    msg_id = Column(Integer, unique=True, nullable=False)
    date_added = Column(Date, nullable=False)
    date_posted = Column(Date, nullable=False)
    raw_obj = Column(Text, nullable=False)
    thumb = Column(Text)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topic.id'))

    def __repr__(self):
        return (f"<Message(id={self.id}, name={self.name}, msg_id"
                f"={self.msg_id}, date_added={self.date_added}, "
                f"date_posted={self.date_posted}, raw_obj={self.raw_obj}, "
                f"thumb={self.thumb}, tg_ch_id={self.tg_ch_id}, topic_id"
                f"={self.topic_id})>")


class MonitoredChannel(Base):
    __tablename__ = 'monitored_channel'

    ch_id = Column(Integer, ForeignKey('channel.id'), primary_key=True)
    date_added = Column(Date)
    date_last_updated = Column(Date)
    is_active = Column(Integer)

    def __repr__(self):
        return (f"<MonitoredChannel(ch_id={self.ch_id}, date_added"
                f"={self.date_added}, date_last_updated"
                f"={self.date_last_updated}, is_active={self.is_active})>")


class TelegramChannel(Base):
    __tablename__ = 'channel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ch_name = Column(String(255))
    ch_id = Column(Integer, unique=True, nullable=False)
    raw_obj = Column(Text)
    date_added = Column(Date)
    date_last_updated = Column(Date)
    last_msg_id = Column(Integer, ForeignKey('message.id'))

    def __repr__(self):
        return (f"<TelegramChannel(id={self.id}, ch_name={self.ch_name}, "
                f"ch_id={self.ch_id}, raw_obj={self.raw_obj}, date_added"
                f"={self.date_added}, date_last_updated"
                f"={self.date_last_updated}, last_msg_id={self.last_msg_id})>")


class Topic(Base):
    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255))
    topic_id = Column(Integer)
    date_added = Column(Date)
    raw_obj = Column(Text)
    tg_ch_id = Column(Integer, ForeignKey('channel.id'))

    def __repr__(self):
        return (f"<Topic(id={self.id}, topic_name={self.topic_name}, "
                f"topic_id={self.topic_id}, date_added={self.date_added}, "
                f"raw_obj={self.raw_obj}, tg_ch_id={self.tg_ch_id})>")


class DLFolder(Base):
    __tablename__ = 'dl_folder'

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text)
    date_added = Column(Date)
    tags = Column(Text)

    def __repr__(self):
        return (f"<DLFolder(id={self.id}, folder_path={self.folder_path}, "
                f"date_added={self.date_added}, tags={self.tags})>")


class DLFile(Base):
    __tablename__ = 'dl_file'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    msg_id = Column(Integer, unique=True)
    date_added = Column(Date)
    path = Column(Text)
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


class DBHelper:
    def __init__(self, database_url: str,
                 pool_size: int = 15,
                 max_overflow: int = 32):
        self.db_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine = create_async_engine(database_url)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

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

    async def update_record(self, table, record_id: int, new_name: str):
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(table).filter(table.id == record_id))
                record = result.scalars().first()
                if record:
                    record.name = new_name
                    await session.commit()

    async def delete_record(self, table, record_id: int):
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(table).filter(table.id == record_id))
                record = result.scalars().first()
                if record:
                    await session.delete(record)
                    await session.commit()

    async def list_records(self, table) -> Sequence[DeclarativeMeta]:
        async with self.async_session() as session:
            result = await session.execute(select(table))
            records = result.scalars().all()
            return records





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
            log("REQUIRED: MYSQL_HOST environment variable not set, using localhost.", level="ERROR")
            host = 'localhost'
        else:
            host = environ['MYSQL_HOST']
        if 'DB_PORT' not in environ:
            log("DB_PORT environment variable not set, using 3306.",
                level="ERROR")
            port = 5432
        else:
            port = environ['MYSQL_PORT']
        if 'DB_DATABASE' not in environ:
            log("REQUIRED: DB_DATABASE environment variable not set, "
                "quitting.", level="ERROR")
            exit(1)
        db = environ['MYSQL_DATABASE']
        database_url = f"postgres://{user}:{password}@{host}:{port}/{db}"
    dbh = DBHelper(database_url)
    dbh.create_database()
    environ['DATABASE_URL'] = database_url
