import logging.config
import json
import pathlib
import os

logging_path = pathlib.Path(os.environ.get('SYNC_LOG_CONFIG', "logging.json"))
if logging_path.exists():
    with logging_path.open() as fd:
        config = json.load(fd)

    logging.config.dictConfig(config)
