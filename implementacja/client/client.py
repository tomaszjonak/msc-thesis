import json
import logging
import queue
import argparse

from heartbeat_service import HeartBeatThread
from labview_connector import LabviewPassiveConnectorThread, LabviewActiveConnectorThread
import sender_service

# TODO(jonak) connection reset handling


def thread_exec(config):
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
            if sender_config['use_compression']:
                services.append(sender_service.CompressingSenderThread(sender_config, filename_queue))
            else:
                services.append(sender_service.FileSenderThread(sender_config, filename_queue))

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


def main():
    parser = argparse.ArgumentParser(description='TODO make some description')
    parser.add_argument('--config', '-c', action='store', default='etc/client_config.json')
    parser.add_argument('--options', '-o', action='append', nargs=2, metavar=('config.part.field', 'value'),
                        help='this can be used multiple times to override config options')

    args = parser.parse_args()

    with open(args.config, 'r') as fd:
        config = json.load(fd)

    # Loop below overrides values in config based on scope
    # i.e providing -o Sender.host '192.168.0.1' results in
    # config['Sender']['host'] = '192.168.0.1'
    # TODO: check whether this loop could be simplified
    # TODO: new value should be converted into type of original one
    for scope_str, value in args.options or []:
        scope = scope_str.split('.')
        curr = None
        try:
            for config_part in scope[:-1]:
                curr = config[config_part]
            curr[scope[-1]] = value
        except KeyError as e:
            print('Undefined config section (section: {}, tag: {}, value: {})'
                  .format(e, repr(scope_str), value))
            exit(-1)

    thread_exec(config)


if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logger.info("Starting up")

    main()
