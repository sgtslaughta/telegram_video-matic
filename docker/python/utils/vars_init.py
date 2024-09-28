from os import environ
from .log_utils import log


def get_vars():
    try:
        with open('../vars.txt') as f:
            for line in f:
                key, value = line.strip().split('=')
                environ[key] = value
        environ['DB_URL'] = _create_db_url()
    except KeyboardInterrupt as e:
        log(str(e), 'error')


def _create_db_url():
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
