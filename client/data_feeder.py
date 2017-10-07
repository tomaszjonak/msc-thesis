from datetime import datetime
import json
import socket
import shutil
import logging
import pathlib
import random
import socketserver


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

    def handle(self):
        logger.info("Connection from {}".format(self.client_address))
        work(self.request, self.extensions, self.root_path)


def send_all(sock, data):
    if isinstance(data, bytes):
        buffer = data
    else:
        buffer = bytes(data, 'utf-8')

    while buffer:
        sent = sock.send(buffer)
        logger.debug('Sent {} bytes'.format(sent))
        buffer = buffer[sent:]


def work(sock, extensions, root_path):
    while True:
        print()
        ok = input("Next?")
        current_time = datetime.now()
        folder_name = current_time.strftime('M%y%m%d')
        file_name = current_time.strftime('M%y%m%d-%H%M%S')
        # file_path = os.path.join(folder_path, file_name)
        folder = pathlib.Path(root_path, folder_name)
        folder.mkdir(exist_ok=True, parents=True)
        file_pattern = folder.joinpath(file_name)
        try:
            for extension in extensions:
                if random.choice((True, True)):
                    file = file_pattern.with_suffix('.{}'.format(extension))
                    shutil.copy('sample_data/pan-tadeusz-czyli-ostatni-zajazd-na-litwie.txt', str(file))
                    # file.symlink_to('data_sample_big.txt')
                    logger.debug('Created {}'.format(str(file)))
                else:
                    logger.debug('Skipped extension ({})'.format(extension))
                # with open(file_path, 'wb') as fd:
                    # fd.write(os.urandom(file_bytes_size))

            send_all(sock, (str(file_pattern) + '\n').encode('utf8'))
            logger.info("Sent {}".format(file_name))
        except ConnectionAbortedError:
            logger.error('Connection aborted by remote host')
            break
        else:
            pass
            # time.sleep(config['interval'])


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
