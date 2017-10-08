from datetime import datetime
import json
import socket
import shutil
import logging
import pathlib
import random
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
        print()
        ok = input("Next?")
        try:
            _work(sock, extensions, root_path, **kwargs)
        except ConnectionAbortedError:
            logger.error('Connection aborted by remote host')
            break
        else:
            pass
            # time.sleep(config['interval'])


def _work(sock, extensions, root_path, **kwargs):
    seeds, paths = get_file_paths(extensions, root_path, **kwargs)
    source_path = kwargs.get('source_path', 'sample_data/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt')
    create_files(paths, source_path)
    # payload, list of path strings separated by \n
    payload = ('\n'.join(str(path) for path in seeds) + '\n').encode('utf8')
    send_all(sock, payload)
    logger.info("Sent {}".format(paths))


def get_file_paths(extensions: list, root_path: str, **kwargs):
    current_time = datetime.now()
    folder_name = current_time.strftime('M%y%m%d')
    file_name_seed = current_time.strftime('M%y%m%d-%H%M%S')

    folder_path = pathlib.Path(root_path, folder_name)
    folder_path.mkdir(exist_ok=True, parents=True)

    names = (file_name_seed + '_{}'.format(rep) for rep in range(kwargs.get('repetitions', 1)))
    seeds = [folder_path.joinpath(name) for name in names]

    paths = [seed.with_suffix(".{}".format(extension)) for seed, extension
             in itertools.product(seeds, extensions)]
    return seeds, paths


def create_files(paths, source_path):
    for path in paths:
        shutil.copy(str(source_path), str(path))


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

    # file_bytes_size = config['file_size']

    work(sock, extensions, root_path)


def run_listening(config: dict):
    passive_config = config['passive_feeder']
    address = passive_config['listening_host'], int(passive_config['listening_port'])
    with DataGeneratorServer(address, DataGeneratorHandle, config) as server:
        logger.info('Listening on {}'.format(address))
        server.serve_forever()


def main():
    with open('etc/feeder_config.json', 'r') as fd:
        config = json.load(fd)

    run_listening(config)


if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
