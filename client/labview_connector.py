import threading
import socketserver
import logging
import pathlib
logger = logging.getLogger(__name__)


class LabviewReceiverHandle(socketserver.BaseRequestHandler):
    def setup(self):
        self.config = self.server.config

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
        target = pathlib.Path(str(data, 'utf8'))

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


class LabviewReceiverThread(threading.Thread):
    def __init__(self, config, queue):
        self.config = config
        self.queue = queue
        self.serving_address = config['listening_host'], int(config['listening_port'])

        super(LabviewReceiverThread, self).__init__()
        self.name = 'LabviewReceiverThread'

    def run(self):
        with LabviewReceiverServer(self.serving_address, LabviewReceiverHandle, self.config, self.queue) as server:
            logger.info('Starting LabviewReceiver, listening on {}'.format(self.serving_address))
            server.serve_forever()
