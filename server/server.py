import socketserver
import json
import os
import logging
import pathlib as pl

# TODO(jonak) connection reset handling
# TODO(jonak) heartbeat logic
# TODO(jonak) refactor that FileTransferTcpHandler._handle


class FileTransferTcpServer(socketserver.TCPServer):
    def __init__(self, server_address, handler_cls, config):
        self.config = config
        super(FileTransferTcpServer, self).__init__(server_address, handler_cls)


class FileTransferTcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            self._handle()
        except ConnectionResetError as e:
            logger.warning('Client connection broken')
            logger.debug('Reason: {}'.format(repr(e)))

    def setup(self):
        self.chunk_size = self.server.config['chunk_size']
        self.destination_folder = self.server.config['destination_folder']

    def _handle(self):
        logger.info('Connection received from {}'.format(self.client_address))
        buffer = bytearray()
        separator = bytes('\r\n', 'ascii')
        while True:
            data = self.request.recv(self.chunk_size)
            buffer += data
            pos = buffer.find(separator)
            if pos == -1:
                logger.debug('Name finding failure')
                continue
            name, buffer = buffer[:pos], buffer[pos + 2:]
            if not len(name):
                continue
            file_windows_path = pl.PureWindowsPath(name.decode('ascii'))
            logger.info('Downloading [{}]...'.format(file_windows_path))
            pos = buffer.find(separator)
            while pos == -1:
                logger.debug('Waiting for len part')
                data = self.request.recv(self.chunk_size)
                buffer += data
                pos = buffer.find(separator)
            data_len, buffer = buffer[:pos], buffer[pos + 2:]
            data_len = int(data_len)
            logger.debug('Incoming data len ({})'.format(data_len))
            written_bytes = 0
            file_path = pl.PurePosixPath(self.destination_folder, file_windows_path)
            os.makedirs(str(file_path.parent), exist_ok=True)
            with open(str(file_path), 'ab') as fd:
                while buffer and written_bytes < data_len:
                    written = fd.write(buffer)
                    written_bytes += written
                    buffer = buffer[written:]
                logger.debug('buffer empty')
                while written_bytes < data_len:
                    chunk = self.request.recv(self.chunk_size)
                    written = fd.write(chunk)
                    written_bytes += written
                logger.info('File [{}], {} bytes written to disk'
                            .format(str(file_path), written_bytes))


def main():
    with open('server_config.json', 'r') as fd:
        config = json.load(fd)

    server_address = config['server_host'], config['server_port']
    destination_folder = config['destination_folder']

    server = socketserver.TCPServer(server_address, FileTransferTcpHandler)
    server.destination_folder = destination_folder
    server.config = config
    logger.info('Listening on {}'.format(server_address))
    server.serve_forever()

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
