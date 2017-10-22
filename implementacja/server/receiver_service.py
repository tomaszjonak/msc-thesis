import json
import logging
import pathlib
import sys

from utility import DeviceProxy

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


class ReceiverStateMachine(object):
    """
    Shallow protocol built on tcp to send and receive files.
    Does not provide data integrity or sync yet.
    """
    def __init__(self, input_device, config):
        # Prepare socket or any other medium supporting read
        self._device = DeviceProxy(input_device, config['separator'], config['chunk_size'])

        # get protocol specific settings
        self.path_parents_to_keep = int(config['path_parents_to_keep'])
        self.base_path = pathlib.Path(config['destination_folder'])
        # Create destination folder and all parents if necessary
        self.base_path.mkdir(exist_ok=True, parents=True)

        # state machine variables
        self._current_file = None
        self._current_len = None
        self._dest_fd = None
        self._bytes_left = None

        # next (initial) state to execute
        self.operation = self._seek_filename

    def run(self):
        while True:
            self.operation()

    def _seek_filename(self):
        name_bytes = self._device.get_token()
        if not len(name_bytes):
            return
        received_path = pathlib.Path(name_bytes.decode('utf8'))
        logger.info('Receiving file ({})'.format(repr(received_path)))

        if any(map(lambda x: len(x) > 255, received_path.parts)):
            raise RuntimeError('Invalid parts in path [{}]'.format(str(received_path)))

        shrinked_path = path_relative_to_nth_parent(received_path, self.path_parents_to_keep)
        logger.debug('Saving as ({})'.format(repr(shrinked_path.parts)))

        self._current_file = self.base_path.joinpath(shrinked_path)
        self.operation = self._seek_size

    def _seek_size(self):
        len_encoded = self._device.get_token()
        self._current_len = int(len_encoded)
        self._bytes_left = self._current_len

        self.operation = self._open_dest
        logger.debug('Found size ({})'.format(self._current_len))

    def _open_dest(self):
        # In case of this work - if file is first in the day it should create folder beforehand
        self._current_file.parent.mkdir(exist_ok=True, parents=True)
        self.dest_fd = self._current_file.open('wb')
        self.operation = self._consume_data
        logger.debug('File created')

    def _close_dest(self):
        self.dest_fd.close()
        self.operation = self._seek_filename
        logger.debug('File saved ({} bytes written)'.format(self._current_file.stat().st_size))
        self._current_len = None
        self._current_file = None

    def _consume_data(self):
        bytes_left = self._current_len
        chunk_size = 8192
        while bytes_left > 0:
            chunk = self._device.get_bytes(chunk_size=chunk_size)
            write_all(self.dest_fd, chunk)
            bytes_left -= len(chunk)
            if chunk_size > bytes_left:
                chunk_size = bytes_left
        self.operation = self._close_dest


def main():
    config_name = 'etc/protocol.json'
    with open(config_name, 'r') as config_fd:
        config = json.load(config_fd)

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'test_data/test2files.data'

    with open(file_path, 'rb') as source_fd:
        machine = ReceiverStateMachine(source_fd, config)
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
