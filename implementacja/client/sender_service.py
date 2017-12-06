import logging
import socket
import threading
import time

from wavelet_compression import wavelet_lvm

logger = logging.getLogger(__name__)


class FileSenderThread(threading.Thread):
    def __init__(self, config, filename_queue):
        self.server_address = config['host'], int(config['port'])
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
        except (ConnectionRefusedError, TimeoutError):
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
        logger.info('Fetching next file...')
        file = self.queue.get()
        logger.info('Processing {}'.format(str(file)))

        file_len = file.stat().st_size
        data_chunk = bytes(str(file) + '\r\n' + str(file_len) + '\r\n', 'utf8')
        try:
            with file.open(mode='rb') as fd:
                while data_chunk:
                    self.socket.send(data_chunk)
                    data_chunk = fd.read(self.chunk_size)
            self.socket.send(bytes('\r\n', 'utf8'))
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError) as e:
            # TODO: ConnectionResetError - handling of file broken in half
            logger.error("Sending interrupted ({})".format(repr(e)))
            self.operation = self.try_connect
            time.sleep(self.connection_retry_interval)
        finally:
            self.queue.task_done()


class CompressingSenderThread(FileSenderThread):
    converters = {'lvm': wavelet_lvm.encode_file}

    def __init__(self, config, filename_queue):
        super(CompressingSenderThread, self).__init__(config, filename_queue)
        self.extensions_to_compress = config['compress']
        self.counter = 0

    def work(self):
        logger.debug('Waiting for file...')
        file = self.queue.get()
        file_name = str(file)
        logger.debug('Processing {}'.format(file_name))

        suffix = file.suffix.lstrip('.')
        # if suffix in self.extensions_to_compress:
        #     if suffix not in self.converters.keys():
        #         logger.warning('Configured to compress {} files but no converters available, sending plain'
        #                        .format(suffix))
        #         bytes_ = file.read_bytes()
        #     else:
        #         bytes_ = self.converters[suffix](file_name)
        #         logger.info('Shrinked file from {} to {} bytes'
        #                     .format(file.stat().st_size, len(bytes_)))
        # else:
        #     bytes_ = file.read_bytes()

        try:
            logger.debug("Sending {}".format(file_name))
            if suffix in self.converters.keys():
                bytes_ = self.converters[suffix](file_name)
                logger.info('Shrinked file from {} to {} bytes'
                            .format(file.stat().st_size, len(bytes_)))
                self.raw_send(file_name, bytes_)
            else:
                self.chunked_send(file)
            # self.raw_send(file_name, bytes_)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError) as e:
            # TODO: ConnectionResetError - handling of file broken in half
            logger.error("Sending interrupted ({})".format(repr(e)))
            self.socket.shutdown()
            self.socket.close()
            self.operation = self.try_connect
            time.sleep(self.connection_retry_interval)
        else:
            self.queue.task_done()
            self.counter += 1
            logger.debug('Sent {} files this far'.format(self.counter))

    def chunked_send(self, file):
        file_len = file.stat().st_size
        data_chunk = bytes(str(file) + '\r\n' + str(file_len) + '\r\n', 'utf8')
        with file.open(mode='rb') as fd:
            while data_chunk:
                self.socket.send(data_chunk)
                data_chunk = fd.read(self.chunk_size)
        self.socket.send(bytes('\r\n', 'utf8'))

    def raw_send(self, file_name, bytes_):
        logger.debug('Sending file ({})'.format(file_name))
        preamble = (file_name + '\r\n' + str(len(bytes_)) + '\r\n').encode('utf8')
        logger.debug('Sending preamble ({})'.format(preamble))
        send_all(self.socket, preamble)
        send_all(self.socket, bytes_)
        # send_all(self.socket, b'\r\n')
        logger.debug('File sent ({})'.format(file_name))


def send_all(socket, data):
    while data:
        sent = socket.send(data)
        data = data[sent:]
