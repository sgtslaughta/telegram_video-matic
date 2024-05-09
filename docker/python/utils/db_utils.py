from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import text
from log_utils import log

Base = declarative_base()


class Message(Base):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    msg_id = Column(Integer)
    date_added = Column(Date)
    raw_data = Column(Text)
    telegram_channel_id = Column(Integer, ForeignKey('telegram_channel.id'))
    topic_id = Column(Integer, ForeignKey('topic.id'))


class TelegramChannel(Base):
    __tablename__ = 'telegram_channel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String(255))
    ch_id = Column(Integer)
    entity_data = Column(Text)
    date_added = Column(Date)


class Topic(Base):
    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(255))
    date_added = Column(Date)
    telegram_channel_id = Column(Integer, ForeignKey('telegram_channel.id'))


class DLFolder(Base):
    __tablename__ = 'dl_folder'

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text)
    date_added = Column(Date)
    tags = Column(Text)


class Tags(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(255))


class MessageTags(Base):
    __tablename__ = 'message_tags'

    message_id = Column(Integer, ForeignKey('message.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)


def create_database(database_url: str):
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
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        new_session = sessionmaker(bind=engine)
        session = new_session()

        # Commit the transaction
        session.commit()

        log(f"Database '{engine.url.database}': connected successfully.", level="SUCCESS")
    except Exception as e:
        log(f"Error connecting to database: {e}", level="ERROR")


def execute_db_command(database_url: str, execute_str: str):
    """
    Execute a database command.
    :param database_url:
    :param execute_str:
    :return:
    """
    try:
        engine = create_engine(database_url)
        new_session = sessionmaker(bind=engine)
        session = new_session()

        # Execute the query
        result = session.execute(text(execute_str))
        # Fetch all rows from the result
        result = result.fetchall()

        # You can return rows or do further processing here
        return result
    except Exception as e:
        log(f"Error querying table: {e}", level="ERROR")


def insert_into_table(database_url: str, table_cls: DeclarativeMeta, **kwargs):
    try:
        engine = create_engine(database_url)
        new_session = sessionmaker(bind=engine)
        session = new_session()

        # Create a new instance of the table class
        new_row = table_cls(**kwargs)

        # Add the new_row to the session
        session.add(new_row)

        # Commit the transaction to persist the changes to the database
        session.commit()

        log(f"Data inserted into: '{table_cls.__tablename__}' successfully.", level="SUCCESS")
        session.close()
    except Exception as e:
        log(f"Error inserting data into table: {e}", level="ERROR")


def modify_row(database_url: str, table_cls: type, primary_key_value: int, **kwargs):
    """
    Modify a row in a database table.

    Args:
        database_url (str): The URL of the database.
        table_cls (type): The SQLAlchemy model representing the table.
        primary_key_value (int): The primary key value of the row to modify.
        **kwargs: Keyword arguments representing the attributes to update and their new values.

    Returns:
        None: This function does not return anything.

    Raises:
        Exception: If there is an error modifying the row.

    Example:
        database_url = 'sqlite:///example.db'
        primary_key_value = 1
        update_data = {'name': 'New Name', 'size': 200, 'date_added': datetime.now()}
        modify_row(database_url, Message, primary_key_value, **update_data)
    """
    try:
        engine = create_engine(database_url)
        new_session = sessionmaker(bind=engine)
        session = new_session()

        # Retrieve the row to modify
        row_to_modify = session.query(table_cls).filter(table_cls.id == primary_key_value).first()

        # Update the attributes of the row
        for key, value in kwargs.items():
            setattr(row_to_modify, key, value)

        # Commit the transaction to persist the changes to the database
        session.commit()

        log("Row modified successfully.", level="SUCCESS")
        session.close()

    except Exception as e:
        log(f"Error modifying row: {e}", level="ERROR")


def delete_rows(database_url: str, table_cls: type, where_clause: str):
    """
    Delete rows from a database table based on a where clause.

    Args:
        database_url (str): The URL of the database.
        table_cls (type): The SQLAlchemy model representing the table.
        where_clause (str): The WHERE clause of the SQL query.

    Returns:
        None: This function does not return anything.

    Raises:
        Exception: If there is an error deleting rows.

    Example:
        database_url = 'sqlite:///example.db'
        where_clause = "size > 100"
        delete_rows(database_url, Message, where_clause)
    """
    try:
        engine = create_engine(database_url)
        new_session = sessionmaker(bind=engine)
        session = new_session()

        # Construct the delete query
        delete_query = f"DELETE FROM {table_cls.__tablename__} WHERE {where_clause}"

        # Execute the delete query
        session.execute(text(delete_query))

        # Commit the transaction to persist the changes to the database
        session.commit()

        log("Rows deleted successfully.", level="SUCCESS")
        session.close()

    except Exception as e:
        log(f"Error deleting rows: {e}", level="ERROR")



db = 'sqlite:///test.db'
from datetime import datetime
now = datetime.now()
q_str = "SELECT * FROM message"
msgs = execute_db_command(db, q_str)
for msg in msgs:
    print(msg.name, msg.msg_id, msg.date_added, msg.raw_data, msg.telegram_channel_id, msg.topic_id)

delete_rows(db, Message, "msg_id = 123")

msgs = execute_db_command(db, q_str)
for msg in msgs:
    print(msg.name, msg.msg_id, msg.date_added, msg.raw_data, msg.telegram_channel_id, msg.topic_id)