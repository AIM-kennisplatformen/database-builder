from loguru import logger
from tqdm import tqdm

from knowledgeplatformmanagement_generic.settings import Configuration


def configure_logger(configuration: Configuration) -> None:
    logger.configure(
        handlers=[
            *(
                (
                    {
                        "backtrace": True,
                        "enqueue": True,
                        "diagnose": False,
                        "format": "{time} - {level} - {name} - {function} - {process} - {thread} - {message}",
                        "level": "DEBUG",
                        "serialize": False,
                        "sink": configuration.paths._path_file_logs,
                    },
                )
                if configuration.paths._path_file_logs.parent.exists()
                else ()
            ),
            {
                "backtrace": False,
                "colorize": True,
                "enqueue": True,
                "diagnose": False,
                "format": "<d>{time}</d> - <red>{level}</red> - {name} - {function} - <b>{message}</b>",
                "serialize": False,
                "sink": lambda message: tqdm.write(message, end=""),
            },
        ],
    )
