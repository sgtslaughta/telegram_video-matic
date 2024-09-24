from datetime import datetime
from sys import stderr, stdout


def log(msg: str, level: str = "INFO") -> None:
    """
    A simple logging function that prints messages to the console.
    Intended to be used in a CLI application or Docker containers.
    :param msg: str - The message to log
    :param level: str - The log level (INFO, WARN, ERROR, SUCCESS)
    :return: None
    """
    yellow = "\033[33m"
    red = "\033[31m"
    green = "\033[32m"
    white = "\033[37m"
    reset = "\033[0m"

    level = level.upper()
    p_level = level.center(7)

    if level == "INFO":
        color = white
    elif level == "WARN":
        color = yellow
    elif level == "ERROR" or level == "FAIL":
        color = red
    elif level == "SUCCESS":
        color = green
    else:
        color = white

    if level == "ERROR":
        file = stderr
    else:
        file = stdout

    d = datetime.now()
    print(f"::[{color}{p_level}{reset}]:: {d} -> {msg}", file=file)
