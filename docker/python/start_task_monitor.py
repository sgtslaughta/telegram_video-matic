import asyncio
from os import environ

from utils.log_utils import log
from utils.svr_tasks import TaskQueue


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


def get_vars():
    try:
        with open('vars.txt') as f:
            for line in f:
                key, value = line.strip().split('=')
                environ[key] = value
    except Exception as e:
        log(str(e), 'error')


async def run_tasks():
    db_url = create_db_url()
    task_queue = TaskQueue(db_url)
    await task_queue.run_tasks()


if __name__ == '__main__':
    asyncio.run(run_tasks())
