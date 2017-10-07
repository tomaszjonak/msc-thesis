import json
import logging
import queue

from heartbeat_service import HeartBeatThread
from labview_connector import LabviewPassiveConnectorThread, LabviewActiveConnectorThread
from sender_service import FileSenderThread

# TODO(jonak) connection reset handling


def main():
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logger.info("Starting up")
    with open('etc/client_config.json', 'r') as fd:
        config = json.load(fd)
    logger.debug("Config read")
    logger.debug("Config contents\n {}".format(json.dumps(config, indent=2)))

    filename_queue = queue.Queue(config["queue_size"])
    logger.debug("Filename queue created")

    sender_config = config['Sender']
    heartbeat_config = config['HeartBeat']
    active_connector_config = config['LabviewActiveConnector']
    passive_connector_config = config['LabviewPassiveConnector']

    services = []
    try:
        if heartbeat_config['enabled']:
            logger.info('Heartbead enabled')
            services.append(HeartBeatThread(heartbeat_config))

        if sender_config['enabled']:
            logger.info('Sender enabled')
            services.append(FileSenderThread(sender_config, filename_queue))

        if passive_connector_config['enabled']:
            logger.info('Passive receiver enabled')
            services.append(LabviewPassiveConnectorThread(passive_connector_config, filename_queue))

        if active_connector_config['enabled']:
            logger.info('Active receiver enabled')
            services.append(LabviewActiveConnectorThread(active_connector_config, filename_queue))

        [service.start() for service in services]
    except Exception as e:
        logger.exception(e)
        exit()
    else:
        [service.join() for service in services]


if __name__ == '__main__':
    main()
