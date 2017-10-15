import logging
import pathlib
import socketserver
import threading

from utility import workers
from utility.device_helpers import DeviceProxy

logger = logging.getLogger(__name__)


class LabviewReceiverHandle(socketserver.BaseRequestHandler):
    def setup(self):
        self.config = self.server.config
        self.base_path = pathlib.Path(self.config['base_path'])

    def handle(self):
        logger.info('Connection received from {}'.format(self.client_address))
        try:
            while True:
                self._handle()
        except ConnectionResetError as e:
            logger.warning("Connection broken by labview")
            logger.debug('Reason: {}'.format(repr(e)))
        except Exception as e:
            logger.warning('{}'.format(repr(e)))

    # TODO(jonak) do i want warning when no files match pattern?
    def _handle(self):
        data = self.request.recv(self.server.config['chunk_size'])
        logger.debug('Received {}'.format(repr(data)))
        target = self.base_path.joinpath(str(data, 'utf8'))

        if not target.parent.exists() or not target.parent.is_dir():
            logger.warning('Received path to nonexistent directory ({})'
                           .format(str(target.parent)))
            return

        files = self.find_matching_files(target)
        for file in files:
            logger.debug('Queueing {}'.format(str(file)))
            self.server.queue.put(file)

    def find_matching_files(self, target):
        filetypes = self.config['filetypes']
        return (file for file in (target.with_suffix('.{}'.format(ext)) for ext in filetypes) if file.exists())


class LabviewReceiverServer(socketserver.TCPServer):
    def __init__(self, server_address, handler_cls, config, queue):
        self.config = config
        self.queue = queue
        super(LabviewReceiverServer, self).__init__(server_address, handler_cls)


class LabviewPassiveConnectorThread(threading.Thread):
    def __init__(self, config, queue):
        self.config = config
        self.queue = queue
        self.serving_address = config['listening_host'], int(config['listening_port'])

        super(LabviewPassiveConnectorThread, self).__init__()
        self.name = 'PassiveReceiverThread'

    def run(self):
        with LabviewReceiverServer(self.serving_address, LabviewReceiverHandle, self.config, self.queue) as server:
            logger.info('Starting LabviewReceiver, listening on {}'.format(self.serving_address))
            server.serve_forever()


class LabviewActiveConnectorThread(workers.KeepAliveWorker):
    def __init__(self, config, queue):
        # Configurables
        self.chunk_size = config['chunk_size']
        self.base_path = pathlib.Path(config.get('base_path', ''))
        self.filetypes = config['filetypes']
        self.delimiter = bytes(config['delimiter'], 'utf8')
        # Destination queue
        self.queue = queue
        # State storage
        self.buffer = bytearray()
        super(LabviewActiveConnectorThread, self).__init__(config)
        self.name = "ActiveReceiverThread"

    def work(self):
        device = DeviceProxy(self.socket, self.delimiter, self.chunk_size)
        while True:
            self._work(device)

    def _work(self, device):
        encoded_path = device.get_token()
        if not encoded_path:
            logger.warning('Encountered empty path token, dropping')
        # logger.debug("Encoded path: {}".format(encoded_path))
        str_path = encoded_path.decode('utf8')
        logger.debug("Got path base ({})".format(str_path))
        path_base = self.base_path.joinpath(str_path)
        # logger.debug("Path base: {}".format(path_base))
        valid_paths = self.find_matching_files(path_base)

        for path in valid_paths:
            self.queue.put(path)
            logger.debug("Queued: {}".format(path))

    def _work_old(self):
        chunk = self.socket.recv(self.chunk_size)
        self.buffer += chunk

        # 1. find all \n terminated sequences
        # 2. remove such from buffer and decode
        # TODO: check path validity needed?
        # 3. add each to queue
        pos = self.buffer.find(self.delimiter)
        while pos != -1:
            encoded_path, self.buffer = self.buffer[:pos], self.buffer[pos + len(self.delimiter):]
            # skip empty entries which may be found on buffer boundary
            if not len(encoded_path):
                continue
            path_base = self.base_path.joinpath(encoded_path.decode('utf8'))
            logger.debug('Path found [{}]'.format(encoded_path.decode('utf8')))
            paths = self.find_matching_files(path_base)

            for path in paths:
                self.queue.put(path)
                logger.debug("Queued [{}]".format(str(path)))

            pos = self.buffer.find(self.delimiter)

    def find_matching_files(self, target):
        return (file for file in (target.with_suffix('.{}'.format(ext)) for ext in self.filetypes) if file.exists())
