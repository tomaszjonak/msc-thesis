import logging.config
import json

with open('logging.json') as fd:
    config = json.load(fd)

logging.config.dictConfig(config)
