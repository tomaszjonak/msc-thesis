from datetime import datetime
import json
import socket
import shutil
import logging
import pathlib
import socketserver
import itertools


class DataGeneratorServer(socketserver.TCPServer):
    """
    Class responsible for data generation on user demand, testing purposes mostly
    """
    def __init__(self, server_address, handler_cls, config):
        self.config = config
        super(DataGeneratorServer, self).__init__(server_address, handler_cls)


class DataGeneratorHandle(socketserver.BaseRequestHandler):
    def setup(self):
        self.config = self.server.config
        self.extensions = [extension.lstrip('.') for extension
                           in self.config['extensions']]
        self.root_path = self.config['path']
        self.repetitions = self.config['passive_feeder']\
                               .get('repetitions', 1)
        self.source_path = self.config['passive_feeder']\
                               .get('source_path', 'sample_data/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt')

    def handle(self):
        logger.info("Connection from {}".format(self.client_address))
        try:
            work(self.request, self.extensions, self.root_path,
                 repetitions=self.repetitions, source_path=self.source_path)
        except ConnectionResetError:
            logger.warning('{} closed connection (reset)'.format(self.client_address))


def send_all(sock, data):
    if isinstance(data, bytes):
        buffer = data
    else:
        buffer = bytes(data, 'utf-8')

    while buffer:
        sent = sock.send(buffer)
        logger.debug('Sent {} bytes'.format(sent))
        buffer = buffer[sent:]


def work(sock, extensions, root_path, **kwargs):
    while True:
        res = input("Next?")

        if res:
            break

        try:
            _work(sock, extensions, root_path, **kwargs)
        except ConnectionAbortedError:
            logger.error('Connection aborted by remote host')
            break


def _work(sock, extensions, root_path, **kwargs):
    seed, paths = get_file_paths(extensions, root_path)
    source_path = kwargs.get('source_path', 'sample_data/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt')
    create_files(paths, source_path)
    # payload, list of path strings separated by \n
    logger.debug(seed.relative_to(root_path).as_posix())
    payload = (seed.relative_to(root_path).as_posix() + '\n').encode('utf8')
    send_all(sock, payload)
    logger.info("Sent {}".format(seed))


def get_file_paths(extensions: list, root_path: str):
    current_time = datetime.now()
    folder_name = current_time.strftime('M%y%m%d')
    file_name_seed = current_time.strftime('M%y%m%d-%H%M%S')

    folder_path = pathlib.Path(root_path, folder_name)
    folder_path.mkdir(exist_ok=True, parents=True)

    seed = folder_path.joinpath(file_name_seed)

    paths = [seed.with_suffix(".{}".format(extension)) for extension in extensions]
    return seed, paths


def create_files(paths, source_path):
    for path in paths:
        shutil.copy(str(source_path), str(path))
        print('Creating {}'.format(path.resolve()))


def run_connecting(config: dict):
    address = config['receiver_host'], int(config['receiver_port'])

    root_path = config['path']
    extensions = [extension.lstrip('.') for extension in config['extensions']]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

    try:
        sock.connect(address)
    except ConnectionRefusedError:
        logger.error('Couldn\'t connect to specified host')
        return

    logger.info('Connected as {}'.format(socket.gethostname()))

    work(sock, extensions, root_path)


def run_listening(config: dict):
    passive_config = config['passive_feeder']
    address = passive_config['listening_host'], int(passive_config['listening_port'])
    server = DataGeneratorServer(address, DataGeneratorHandle, config)
    logger.info('Listening on {}'.format(address))
    server.serve_forever()


def main():
    with open('feeder_config.json', 'r') as fd:
        config = json.load(fd)

    run_listening(config)


if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
