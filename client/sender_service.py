import threading
import socket
import time
import logging
logger = logging.getLogger(__name__)


class FileSenderThread(threading.Thread):
    def __init__(self, config, filename_queue):
        self.server_address = config['server_fqdn'], int(config['server_port'])
        self.queue = filename_queue
        self.chunk_size = config['chunk_size']
        self.connection_retry_interval = config['connection_retry_interval']

        self.socket = None

        self.operation = self.try_connect
        super(FileSenderThread, self).__init__()
        self.name = 'FileSenderThread'

    def try_connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(self.server_address)
        except ConnectionRefusedError:
            logger.warning('{} refused connection, sleeping for {} sec'
                           .format(self.server_address, self.connection_retry_interval))
            time.sleep(self.connection_retry_interval)
        else:
            logger.info('Connection to {} estabilished'
                        .format(self.server_address))
            self.operation = self.work

    def run(self):
        logger.info('FileSenderThread started')
        while True:
            self.operation()

    def work(self):
        file = self.queue.get()
        logger.info('Processing {}'.format(str(file)))

        file_len = file.stat().st_size
        data_chunk = bytes(str(file) + '\r\n' + str(file_len) + '\r\n', 'ascii')
        try:
            with file.open(mode='rb') as fd:
                while data_chunk:
                    self.socket.send(data_chunk)
                    data_chunk = fd.read(self.chunk_size)
            self.socket.send(bytes('\r\n', 'ascii'))
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError) as e:
            # TODO: ConnectionResetError - handling of file broken in half
            logger.error("Sending interrupted ({})".format(repr(e)))
            self.operation = self.try_connect
            time.sleep(self.connection_retry_interval)
        finally:
            self.queue.task_done()
