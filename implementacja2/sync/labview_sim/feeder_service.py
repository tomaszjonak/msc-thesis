import queue
import socketserver
import logging
import threading

from . import dated_file_generator

FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FeederContorller(object):
    def __init__(self, storage_root, feeder_service=None, address=None, **kwargs):
        self.address = address or ('127.0.0.1', 8887)
        self.service = feeder_service or FeederService(self.address, kwargs.get('queue_timeout', 2))

        self.generator = dated_file_generator.DatedFilesGenerator(
            dir_fmt='M%y%m%d',
            file_fmt='M%y%m%d-%H%M%S',
            storage_root=storage_root,
            extensions=kwargs.get('extensions', ['lvm', 'avi']),
        )

    def create_file(self, path, data_source):
        with open(path, 'wb') as fd:
            fd.write(data_source())

    def announce_file(self, path):
        self.service.announce(path)

    def stop(self):
        self.service.stop()

    def create_dated_files(self):
        return self.generator.generate_file()

    def create_and_announce_dated_files(self):
        file_pattern = self.generator.generate_file()
        self.service.announce(file_pattern)
        return file_pattern

    def next_directory(self, n=1):
        self.generator.next_directory(n)


class FeederService(object):
    def __init__(self, address, queue_timeout, **kwargs):
        self.queue = queue.Queue()
        self.thread = FeederThread(address, self.queue, queue_timeout, **kwargs)
        self.thread.start()

    def announce(self, path):
        self.queue.put(path)

    def stop(self):
        self.thread.shutdown()

    def __del__(self):
        if self.thread.isAlive():
            self.thread.join()


class FeederThread(threading.Thread):
    def __init__(self, address, queue, queue_timeout, **kwargs):
        self.address = address
        self.queue = queue
        self.queue_timeout = queue_timeout
        super(FeederThread, self).__init__()
        self.name = 'FeederThread'

    def run(self):
        self.server = FeederServer(self.address, FeederConnectionHandler, self.queue, self.queue_timeout)
        self.server.serve_forever()

    def shutdown(self):
        self.server.stop = True
        self.server.shutdown()


def send_file(char_device, filename):
    char_device.sendall(filename.encode('utf8'))


class FeederConnectionHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.queue = self.server.queue
        self.timeout = self.server.timeout

    def handle(self):
        try:
            while not self.server.stop:
                try:
                    filename = self.queue.get(timeout=self.timeout)
                    assert(isinstance(filename, str))
                    self.request.sendall((filename + '\n').encode('utf8'))
                except queue.Empty:
                    pass

        except (ConnectionResetError, ConnectionAbortedError) as e:
            logger.warning('{} closed connection ({})'.format(self.client_address, type(e)))


class FeederServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, server_address, handler_cls, queue_, queue_timeout, **kwargs):
        self.queue = queue_
        self.options = kwargs
        self.stop = False
        self.timeout = queue_timeout
        super(FeederServer, self).__init__(server_address, handler_cls)


def main():
    pass

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
