import logging.config
import json
import pathlib

logging_path = pathlib.Path('logging.json')
if logging_path.exists():
    with logging_path.open() as fd:
        config = json.load(fd)

    logging.config.dictConfig(config)
