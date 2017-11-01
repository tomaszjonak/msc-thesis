from . import StreamProxy


class StreamTokenWriter(object):
    """
    Klasa odpowiedzialna za wpisywanie tokenow razem z separatorami do strumienia
    """
    def __init__(self, stream: StreamProxy.StreamProxy, separator: (bytes, bytearray, str)):
        if not isinstance(stream, StreamProxy.StreamProxy):
            raise RuntimeError('Can\'t create StreamTokenWriter with unsupported stream type ({})'.format(type(stream)))
        if not isinstance(separator, (bytes, bytearray, str)):
            raise RuntimeError('Separator has to be either string or bytes (got: )'.format(type(separator)))
        if not separator:
            raise RuntimeError('Can\'t use empty separator')

        self._stream = stream
        self.separator = separator if isinstance(separator, (bytes, bytearray)) else separator.encode('utf8')

    def write_token(self, token, separator=None):
        """
        Wpisuje token razem z separatorem do streamu, token musi byc konwertowalny do bajtow
        """
        if separator:
            separator = separator if isinstance(separator, (bytes, bytearray)) else separator.encode('utf8')
        separator = separator or self.separator

        # In case of none param we want to write empty string with separator (empty token)
        token = token or ''
        token = token if isinstance(token, (bytes, bytearray)) else token.encode('utf8')

        self._stream.write_all(token + separator)

    def write_bytes(self, buffer):
        """
        Wpisuje zawartosc buffora do strumienia
        """
        buffer = buffer if isinstance(buffer, (bytes, bytearray)) else buffer.encode('utf8')
        self._stream.write_all(buffer)

    def write_separator(self, separator=None):
        """
        Wpisuje sam separator
        """
        if separator:
            separator = separator if isinstance(separator, (bytes, bytearray)) else separator.encode('utf8')
        separator = separator or self.separator

        self._stream.write_all(separator)
