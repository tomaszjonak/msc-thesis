import json
import sys
import pathlib
import logging
logger = logging.getLogger(__name__)


def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'little')


def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'little')


def path_relative_to_nth_parent(path, n):
    parts = path.parts
    plen = len(parts)
    if n >= plen:
        return path
    if n < 0:
        raise RuntimeError('')
    shrinked_parts = parts[plen - (n + 1):]
    return pathlib.Path(*shrinked_parts)


class ReciverStateMachine(object):
    def __init__(self, input_device, config):
        self.operation = self._seek_filename
        self.buffer = bytearray()
        self.char_device = input_device
        self.chunk_size = config['chunk_size']
        self.separator = bytes(config['separator'], 'utf8')
        self.path_parents_to_keep = int(config['path_parents_to_keep'])
        self.read_needed = True

        self.current_file = None
        self.current_len = None
        self.dest_fd = None

        self.base_path = pathlib.Path(config['destination_folder'])
        self.base_path.mkdir(exist_ok=True, parents=True)

    def add_to_buffer(self):
        chunk = self.char_device.read(self.chunk_size)
        self.buffer += chunk
        # logger.debug('Read occurred ({} bytes)'.format(len(chunk)))
        if not len(chunk):
            raise RuntimeError('Eof m8')

    def run(self):
        while True:
            if self.read_needed:
                self.add_to_buffer()
            self.operation()

    def _seek_filename(self):
        logger.debug('Seeking filename')
        pos = self.buffer.find(self.separator)
        if pos == -1:
            logger.debug('Not yet in buffer')
            self.read_needed = True
            return

        name, self.buffer = self.buffer[:pos], self.buffer[pos + len(self.separator):]
        if not len(name):
            logger.warning('Found empty name, jumping to next separator')
            return
        received_path = pathlib.Path(name.decode('utf8'))
        logger.info('File incoming [{}]'.format(str(received_path)))
        if any(map(lambda x: len(x) > 255, received_path.parts)):
            raise RuntimeError('Invalid parts in path [{}]'.format(str(received_path)))

        shrinked_path = path_relative_to_nth_parent(received_path, self.path_parents_to_keep)
        self.current_file = self.base_path.joinpath(shrinked_path)
        self.operation = self._seek_size
        self.read_needed = False

    def _seek_size(self):
        pos = self.buffer.find(self.separator)
        if pos != -1:
            len_encoded, self.buffer = self.buffer[:pos], self.buffer[pos + len(self.separator):]
            self.current_len = int(len_encoded)
            self.bytes_left = self.current_len
            logger.debug(self.current_len)
            self.operation = self._open_dest
            self.read_needed = False
        else:
            self.read_needed = True

    def _open_dest(self):
        self.current_file.parent.mkdir(exist_ok=True, parents=True)
        self.dest_fd = self.current_file.open('wb')
        self.operation = self._consume_data

    def _close_dest(self):
        self.dest_fd.close()
        logger.info('[{}] written to disk'.format(str(self.current_file)))
        self.current_len = None
        self.current_file = None
        self.operation = self._seek_filename
        if not len(self.buffer):
            self.read_needed = True

    def _consume_data(self):
        buffer_len = len(self.buffer)
        if buffer_len <= self.bytes_left:
            write_all(self.dest_fd, self.buffer)
            self.bytes_left -= buffer_len
            self.buffer = bytearray()
        else:
            write_all(self.dest_fd, self.buffer[:self.bytes_left])
            self.buffer = self.buffer[self.bytes_left:]
            self.bytes_left -= self.bytes_left

        # logger.debug('{} bytes left...'.format(self.bytes_left))
        # logger.debug('Buffer state [{}]'.format(len(self.buffer)))
        if self.bytes_left <= 0:
            self.operation = self._close_dest
            self.read_needed = False
        else:
            self.read_needed = True


def main():
    config_name = 'etc/protocol.json'
    with open(config_name, 'r') as config_fd:
        config = json.load(config_fd)

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'test_data/test2files.data'

    with open(file_path, 'rb') as source_fd:
        machine = ReciverStateMachine(source_fd, config)
        try:
            machine.run()
        except RuntimeError as e:
            logger.error(e)
        logger.debug('Exittting')


def write_all(fd, buffer):
    while buffer:
        written = fd.write(buffer)
        # logger.debug('Written {}'.format(written))
        buffer = buffer[written:]

if __name__ == '__main__':
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger.setLevel(logging.DEBUG)

    main()
