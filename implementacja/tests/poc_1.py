import socketserver
import logging
logger = logging.getLogger(__name__)


class TestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logger.info('Connection from {}'.format(self.client_address))
        data = self.request.recv(8192)
        while data:
            logger.debug('pre send')
            self.request.sendall(data)
            logger.debug('post send')
            logger.info(data)
            data = self.request.recv(8192)


class TwoWayStateMachine(object):
    def __init__(self, char_device):
        self.char_device = char_device

        self.state = None

    def _state_init(self):
        pass


def main():
    with socketserver.TCPServer(('localhost', 1234), TestHandler) as server:
        server.serve_forever()

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    main()
