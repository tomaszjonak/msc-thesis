import logging
logger = logging.getLogger(__name__)


class RecvToReadProxy(object):
    def __init__(self, recv_device):
        self.device = recv_device

    def read(self, chunk_size):
        return self.device.recv(chunk_size)


class DeviceProxy(object):
    """
    Class to ease working with stream data from device like objects

    calls may are blocking in respect to fetching data in case of network sockets
    """
    # TODO: eof handling
    def __init__(self, char_device, separator, chunk_size):
        """
        :param char_device: something with read method
        :param separator: character separating valid tokens
        """
        if hasattr(char_device, 'read'):
            self._device = char_device
        elif hasattr(char_device, 'recv'):
            self._device = RecvToReadProxy(char_device)
        else:
            raise RuntimeError("Unsupported device type")

        if isinstance(separator, (bytes, bytearray)):
            self.separator = separator
        elif isinstance(separator, str):
            self.separator = separator.encode('utf8')
        else:
            raise RuntimeError("Separator has wrong type ({})".format(type(separator)))

        self._buffer = bytearray()
        self.chunk_size = chunk_size

        self._fetch_from_device()

    def _fetch_from_device(self, chunk_size=None):
        """
        Populates buffer with new data from device
        i.e network socket or file
        :param chunk_size: expected size of single read
        :return:
        """
        chunk_size = chunk_size or self.chunk_size

        # TODO what happens on eof
        chunk = self._device.read(chunk_size)
        # logger.debug("Fetched data from device ({} bytes)".format(len(chunk_size)))
        self._buffer += chunk

    def get_token(self):
        """
        drops found sequence and separator from internal buffer
        :return: first set of bytes terminated by separator (token)
        """

        pos = self._buffer.find(self.separator)
        while pos == -1:
            self._fetch_from_device()

        token = self._buffer[:pos]
        self._buffer = self._buffer[pos + len(self.separator):]

        return token

    def get_bytes(self, chunk_size=None):
        """
        Fetch data from buffer/device
        :param chunk_size: size of one batch of data
        :return: bytes with len specified in `chunk_size`
        """
        chunk_size = chunk_size or self.chunk_size
        if chunk_size > self.chunk_size:
            raise RuntimeError("Exceeding chunk size limit, this may exhaust memory")

        if len(self._buffer) < chunk_size:
            self._fetch_from_device()

        bytes_to_return = self._buffer[:chunk_size]
        self._buffer = self._buffer[chunk_size:]

        return bytes_to_return

    def flush(self):
        self._buffer = bytearray()


def main():
    sample_config = {
        "host": "localhost",
        "port": 6341,

        "chunk_size": 8192,
        "separator": "\n",
        "dest_file": "stats.csv"
    }

    try:
        service = DataHarvester(sample_config)
    except Exception as e:
        logger.exception(e)
    else:
        service.join()

if "__main__" == __name__:
    FORMAT = '%(asctime)s [%(name)s|%(threadName)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    main()
