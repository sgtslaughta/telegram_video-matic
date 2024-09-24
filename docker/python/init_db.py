#!/usr/bin/env python3

import asyncio
from os import environ

from utils.db_utils import DBHelper
from utils.log_utils import log


def get_vars():
    try:
        with open('vars.txt') as f:
            for line in f:
                key, value = line.strip().split('=')
                environ[key] = value
    except Exception as e:
        log(str(e), 'error')


def create_db_url():
    get_vars()
    try:
        user = environ['DB_USER']
        pw = environ['DB_PASS']
        host = environ['DB_HOST']
        name = environ['DB_NAME']
        port = environ['DB_PORT']
    except KeyError as e:
        log(f"Missing environment variable: {e}", 'error')
        exit(1)
    return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{name}"


async def init_db():
    get_vars()
    db = DBHelper(create_db_url())
    await db.create_tables()
    log('Database initialized', 'success')


if __name__ == '__main__':
    asyncio.run(init_db())
