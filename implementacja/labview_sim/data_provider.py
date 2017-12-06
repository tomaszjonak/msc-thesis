import pathlib as pl
import socket
import socketserver
import contextlib
import time
import datetime as dt

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@contextlib.contextmanager
def connection(*args, **kwargs):
    conn = socket.create_connection(*args, **kwargs)
    try:
        yield conn
    finally:
        conn.close()


class DataGeneratorServer(socketserver.TCPServer):
    """
    Class responsible for data generation on user demand, testing purposes mostly
    """
    def __init__(self, server_address, handler_cls, config):
        self.config = config
        super(DataGeneratorServer, self).__init__(server_address, handler_cls)
        self.allow_reuse_address = True


class DataGeneratorHandle(socketserver.BaseRequestHandler):
    def setup(self):
        self.config = self.server.config
        self.extensions = [extension.lstrip('.') for extension
                           in self.config['extensions']]
        self.root_path = self.config['path']

    def handle(self):
        logger.info("Connection from {}".format(self.client_address))
        try:
            work(self.request, self.root_path, self.extensions, sleep=3)
        except ConnectionResetError:
            logger.warning('{} closed connection (reset)'.format(self.client_address))


def work(socket, storage_root, extensions, **kwargs):
    storage_root = pl.Path(storage_root)
    files = storage_root.glob('*.lvm')

    def key(file: pl.Path):
        return dt.datetime.strptime(file.with_suffix('').name, 'M%y%m%d_%H%M%S')

    files_to_send_ = sorted(files, key=key)
    files_to_send = (file.with_suffix('') for file in files_to_send_)

    if 'sleep' in kwargs.keys():
        for file in files_to_send:
            logger.info('Sending {}'.format(str(file)))
            socket.send((str(file) + '\n').encode())
            time.sleep(kwargs['sleep'])
    else:
        for file in files_to_send:
            logger.info('Sending {}'.format(str(file)))
            socket.send((str(file) + '\n').encode())
            input('Next? ')


def main():
    import sys
    address = sys.argv[1], int(sys.argv[2])
    # storage_root = pl.Path('R2017_10_06')

    config = {
        'extensions': sys.argv[4:],
        'path': sys.argv[3],
    }
    logger.info("Starting server")
    server = DataGeneratorServer(address, DataGeneratorHandle, config=config)
    server.serve_forever()


if __name__ == '__main__':
    main()
