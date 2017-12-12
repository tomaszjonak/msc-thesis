from . import StreamProxy


class StreamTokenReaderError(BrokenPipeError):
    pass


class StreamTokenReader(object):
    """
    Klasa odpowiedzialna za manipulacje strumieniem w celu odczytu pojedynczych tokenow ze strumienia

    Pojecia:
    token - pojedyncza informacja bedaca czescia protokolu, strumien tak zaprojektowany sklada sie z elementow
    <token><separator><token><separator>...
    """

    def __init__(self, stream: StreamProxy.StreamProxy, separator: (str, bytes, bytearray), chunk_size: int=8192):
        """
        :param char_device: Instancja klasy StreamProxy
        :param separator: znak/sekwencja znakow rozdzielajacych strumien
        :param chunk_size: wielkosc pojedynczego odczytu
        """
        if not isinstance(stream, StreamProxy.StreamProxy):
            raise RuntimeError('Can\'t create StreamTokenReader with unsupported stream type {}'.format(type(stream)))
        if not isinstance(separator, (str, bytes, bytearray)):
            raise RuntimeError('Can\'t create StreamTokenReader with unsupported separator type {}'
                               .format(type(separator)))
        if not isinstance(chunk_size, int):
            raise RuntimeError('chunk_size have to be unsigned integer bigger than 0 (got: {})'
                               .format(repr(chunk_size)))
        if not separator:
            raise RuntimeError('separator has to be nonempty string (got: {})'.format(repr(separator)))

        self._stream = stream
        self.separator = separator if isinstance(separator, (bytes, bytearray)) else separator.encode('utf8')
        self.chunk_size = chunk_size
        self._buffer = bytearray()
        self.timeout_ = None

    def _fetch_from_device(self, chunk_size=None):
        """
        :param chunk_size:
        :return:
        """
        chunk_size = chunk_size or self.chunk_size

        chunk = self._stream.read(chunk_size)
        if not chunk:
            raise StreamTokenReaderError('End of stream')

        self._buffer += chunk

    def get_token(self, separator=None):
        """
        Zwraca pierwszy token znaleziony w strumieniu i usuwa go z niego razem z separatorem
        :return:
        """
        separator = separator or self.separator

        pos = self._buffer.find(separator)
        while pos == -1:
            self._fetch_from_device()
            pos = self._buffer.find(self.separator)

        token = self._buffer[:pos]
        self._buffer = self._buffer[pos + len(separator):]

        return token

    def get_bytes(self, chunk_size=None):
        """
        :param chunk_size: opcjonalny parametr jesli chcemy pobrac ilosc bajtow inna niz skonfigurowana
        :return: bajty w ilosci rownej chunk_size
        """
        chunk_size = chunk_size or self.chunk_size
        if chunk_size > self.chunk_size:
            raise RuntimeError('Requested chunk_size exceedes configured one, this may exhaoust memory')

        while len(self._buffer) < chunk_size:
            self._fetch_from_device()

        bytes_to_return = self._buffer[:chunk_size]
        self._buffer = self._buffer[chunk_size:]

        return bytes_to_return

    def flush(self):
        """
        :return: zwraca wszystko co zostalo w buforze i go zeruje
        """
        tmp = self._buffer
        self._buffer = bytearray()
        return tmp

    def seek0(self):
        self._stream.seek0()

    @property
    def timeout(self):
        return self.timeout_

    @timeout.setter
    def timeout(self, value):
        self.timeout_ = value
        if isinstance(self._stream, StreamProxy.SocketStreamProxy):
            self._stream.set_timeout(self.timeout_)
