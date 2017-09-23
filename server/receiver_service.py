import json
import sys
import pathlib


def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'little')


def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'little')


class ReciverStateMachine(object):
    def __init__(self, input_device, config):
        self.operation = self._seek_filename
        self.buffer = bytearray()
        self.char_device = input_device
        self.chunk_size = config['chunk_size']
        self.separator = bytes(config['separator'], 'utf8')
        self.read_needed = True

        self.current_file = None
        self.current_len = None
        self.dest_fd = None

        self.base_path = pathlib.Path(config['base_path'])
        self.base_path.mkdir(exist_ok=True)

    def add_to_buffer(self):
        chunk = self.char_device.read(self.chunk_size)
        self.buffer += chunk
        print('Read occurred ({} bytes)'.format(len(chunk)))
        if not len(chunk):
            raise RuntimeError('Eof m8')

    def run(self):
        while True:
            if self.read_needed:
                self.add_to_buffer()
            self.operation()

    def _seek_filename(self):
        print('Seeking filename')
        pos = self.buffer.find(self.separator)
        if pos == -1:
            print('Not yet in buffer')
            self.read_needed = True
            return

        name, self.buffer = self.buffer[:pos], self.buffer[pos + len(self.separator):]
        print('Found')
        win_file_path = pathlib.Path(name.decode('utf8'))
        if any(map(lambda x: len(x) > 255, win_file_path.parts)):
            raise RuntimeError('Invalid parts in path [{}]'.format(str(win_file_path)))
        self.current_file = self.base_path.joinpath(win_file_path)
        self.operation = self._seek_size
        self.read_needed = False

    def _seek_size(self):
        pos = self.buffer.find(self.separator)
        if pos != -1:
            len_encoded, self.buffer = self.buffer[:pos], self.buffer[pos + len(self.separator):]
            self.current_len = int(len_encoded)
            self.bytes_left = self.current_len
            print(self.current_len)
            self.operation = self._open_dest
            self.read_needed = False
        else:
            self.read_needed = True

    def _open_dest(self):
        self.dest_fd = self.current_file.open('wb')
        self.operation = self._consume_data

    def _close_dest(self):
        self.dest_fd.close()
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

        print('{} bytes left...'.format(self.bytes_left))
        print('Buffer state [{}]'.format(len(self.buffer)))
        if self.bytes_left <= 0:
            self.operation = self._close_dest
            self.read_needed = False
        else:
            self.read_needed = True


def main():
    config_name = 'protocol.json'
    with open(config_name, 'r') as config_fd:
        config = json.load(config_fd)

    file_path = sys.argv[1]
    with open(file_path, 'rb') as source_fd:
        machine = ReciverStateMachine(source_fd, config)
        try:
            machine.run()
        except RuntimeError as e:
            print(e)
        print('Exittting')


def write_all(fd, buffer):
    while buffer:
        written = fd.write(buffer)
        print('Written {}'.format(written))
        buffer = buffer[written:]
x
if __name__ == '__main__':
    main()
