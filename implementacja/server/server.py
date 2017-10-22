import json
import logging
import socketserver
import argparse

import receiver_service


# TODO(jonak) connection reset handling
# TODO(jonak) heartbeat logic
# TODO(jonak) argparse startup


class FileTransferTcpServer(socketserver.TCPServer):
    def __init__(self, server_address, handler_cls, protocol_config):
        self.protocol_config = protocol_config
        super(FileTransferTcpServer, self).__init__(server_address, handler_cls)


class RecvProxy(object):
    """
    Duck type class to use read instead of recv
    """
    def __init__(self, socket):
        self.socket = socket

    def read(self, chunk_size):
        return self.socket.recv(chunk_size)


class FileTransferTcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logger.info('Connection from {}'.format(self.client_address))
        try:
            self._handle()
        except ConnectionResetError as e:
            logger.warning('Client connection broken')
            logger.debug('Reason: {}'.format(repr(e)))

    def setup(self):
        self.protocol_config = self.server.protocol_config

    def _handle(self):
        machine = receiver_service.ReceiverStateMachine(RecvProxy(self.request), self.protocol_config)
        try:
            machine.run()
        except ConnectionResetError:
            logger.warning('{} closed connection (reset)'.format(self.client_address))
        except Exception as e:
            logger.error('Exception caught')
            logger.exception(e)


def main():
    parser = argparse.ArgumentParser(description='TODO make some description')
    parser.add_argument('--config', '-c', action='store', default='etc/server_config.json')
    parser.add_argument('--options', '-o', action='append', nargs=2, metavar=('config.part.field', 'value'),
                        help='this can be used multiple times to override config options')

    args = parser.parse_args()

    with open(args.config, 'r') as fd:
        config = json.load(fd)

    # Loop below overrides values in config based on scope
    # i.e providing -o Sender.host '192.168.0.1' results in
    # config['Sender']['host'] = '192.168.0.1'
    # TODO: duplcates code from client.py - do i want separation or code reuse
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

    logger.debug("Config contents\n {}".format(json.dumps(config, indent=2)))
    try:
        service_exec(config)
    except OSError:
        logger.error('Invalid (host, port) provided. Can not proceed')
    except Exception as e:
        logger.exception(e)


def service_exec(config):
    server_config = config['server']
    protocol_config = config['protocol']

    server_address = server_config['host'], int(server_config['port'])

    server = FileTransferTcpServer(server_address, FileTransferTcpHandler, protocol_config)
    logger.info('Listening on {}'.format(server_address))
    server.serve_forever()

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
