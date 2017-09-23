import json
import logging
import queue

from heartbeat_service import HeartBeatThread
from labview_connector import LabviewReceiverThread
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
    logger.debug("Config contents: {}".format(config))

    filename_queue = queue.Queue(config["queue_size"])
    logger.debug("Filename queue created")

    try:
        # heartbeat_service = HeartBeatThread(config)
        # heartbeat_service.start()

        filesender_service = FileSenderThread(config, filename_queue)
        filesender_service.start()

        receiver_service = LabviewReceiverThread(config, filename_queue)
        receiver_service.start()
    except Exception as e:
        logger.error(repr(e))
        exit()
    else:
        receiver_service.join()
        filesender_service.join()
        # heartbeat_service.join()


if __name__ == '__main__':
    main()
