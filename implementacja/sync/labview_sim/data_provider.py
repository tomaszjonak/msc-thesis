import pathlib as pl
import socket
import socketserver
import contextlib
import time
import datetime as dt
import argparse
import logging
import itertools

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
        logger.info('Data provider listening {}'.format(self.server_address))


class DataGeneratorHandle(socketserver.BaseRequestHandler):
    def setup(self):
        self.config = self.server.config
        self.extensions = [extension.lstrip('.') for extension
                           in self.config['extensions']]
        self.root_path = self.config['path']
        self.sleep = self.config['sleep']
        self.skip = self.config['skip']

    def handle(self):
        logger.info("Connection from {}".format(self.client_address))
        try:
            work(self.request, self.root_path, self.extensions, self.sleep, self.skip)
        except ConnectionResetError:
            logger.warning('{} closed connection (reset)'.format(self.client_address))


def work(socket, storage_root, extensions, sleep=0, skip=0):
    storage_root = pl.Path(storage_root)
    chain = []
    for extension in extensions:
        chain = itertools.chain(chain, storage_root.rglob('*.{}'.format(extension)))

    files = [path.relative_to(storage_root).with_suffix('') for path in chain]

    def key(file: pl.Path):
        return dt.datetime.strptime(file.name, 'M%y%m%d_%H%M%S')

    files_to_send = sorted(set(files), key=key)
    logger.info('Found {} files to send'.format(len(files_to_send)))

    if sleep:
        for file in files_to_send[skip:]:
            logger.info('Sending {}'.format(str(file)))
            socket.send((str(file) + '\n').encode())
            time.sleep(sleep)
    else:
        for file in files_to_send:
            x = input('Next? ')
            if x:
                logger.debug('Skipping {}'.format(str(file)))
            else:
                logger.info('Sending {}'.format(str(file)))
                socket.send((str(file) + '\n').encode())
    exit(0)


def main():
    parser = argparse.ArgumentParser(description='Measurement system simulator, plays files from given directory')
    parser.add_argument('--host', '-hs', action='store', required=True, help='host on which provider listens')
    parser.add_argument('--port', '-p', action='store', required=True, type=int, help='port on which provider listens')
    parser.add_argument('--storage_root', '-s', action='store', required=True, help='folder to search files from')
    parser.add_argument('--extensions', '-e', action='store', nargs='+', required=True,
                        help='specifies extensions which will be sent from folder (extension doesnt include dot,'
                             ' doesnt support compund extensions like tar.gz right now)')
    parser.add_argument('--sleep', '-sl', action='store', type=float, default=0,
                        help='if this option is present provider will send files every given seconds')
    parser.add_argument('--skip', '-sk', action='store', type=int, default=0,
                        help='skips sending of given amount of files, used to test synchronization')

    args = parser.parse_args()

    address = args.host, int(args.port)
    config = {
        'extensions': args.extensions,
        'path': args.storage_root,
        'sleep': args.sleep,
        'skip': args.skip
    }

    if args.sleep:
        logger.info('Starting provider in non interactive mode')
    else:
        logger.info('Starting data provider in interactive mode, enter to send file, some keys and enter to skip file')

    try:
        server = DataGeneratorServer(address, DataGeneratorHandle, config=config)
        server.serve_forever()
    except OSError as e:
        if e.errno == 98:
            logger.warning('Socket was closed recently, wait until end of TIME_WAIT state')
        else:
            raise


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n')
        logger.info('SIGINT caught, exitting')
