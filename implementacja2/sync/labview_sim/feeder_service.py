import queue
import socketserver
import logging
import threading

FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FeederContorller(object):
    def __init__(self, feeder_service=None):
        if not feeder_service:
            address = ('127.0.0.1', 8887)
            feeder_service = FeederService(address)
        self.service = feeder_service

    def create_file(self, path, data_source):
        with open(path, 'wb') as fd:
            fd.write(data_source())

    def announce_file(self, path):
        self.service.announce(path)

    def stop(self):
        self.service.stop()


class FeederService(object):
    def __init__(self, address):
        self.queue = queue.Queue()
        self.thread = FeederThread(address, self.queue)
        self.thread.start()

    def announce(self, path):
        self.queue.put(path)

    def stop(self):
        self.thread.shutdown()

    def __del__(self):
        if self.thread.isAlive():
            self.thread.join()


class FeederThread(threading.Thread):
    def __init__(self, address, queue):
        self.address = address
        self.queue = queue
        super(FeederThread, self).__init__()
        self.name = 'FeederThread'

    def run(self):
        self.server = FeederServer(self.address, FeederConnectionHandler, self.queue)
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


def send_file(char_device, filename):
    char_device.sendall(filename.encode('utf8'))


class FeederConnectionHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.queue = self.server.queue

    def handle(self):
        try:
            while True:
                filename = self.queue.get()
                assert(isinstance(filename, str))
                self.request.sendall((filename + '\n').encode('utf8'))

        except (ConnectionResetError, ConnectionAbortedError) as e:
            logger.warning('{} closed connection ({})'.format(self.client_address, type(e)))


class FeederServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, handler_cls, queue_, **kwargs):
        self.queue = queue_
        self.options = kwargs
        super(FeederServer, self).__init__(server_address, handler_cls)


def main():
    pass

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
