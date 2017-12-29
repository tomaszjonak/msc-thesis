import logging.config
import json

# FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)
with open('logging.json') as fd:
    config = json.load(fd)

logging.config.dictConfig(config)
