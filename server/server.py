import socketserver
import json
import logging
import sys
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
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = 'etc/server_config.json'

    with open(config_file, 'r') as fd:
        config = json.load(fd)

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
