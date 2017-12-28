import abc
import pathlib as pl
import tempfile


class StreamProxy(abc.ABC):
    """
    Klasa implementujaca interfejs do wymiany danych. Jej zadaniem jest uwspolnienie
    interfejsow IO dla plikow oraz socketow.
    """
    @abc.abstractmethod
    def read(self, chunk_len: int):
        """
        Odczytaj dane, jesli w buforze nie ma wystarczajaco danych zwroc mniej badz poczekaj na wiecej
        :param chunk_len: maksymalna dlugosc odczytu
        :return: bytes: bufor z odczytanymi danymi
        """
        pass

    @abc.abstractmethod
    def write(self, buffer):
        """
        Zapisz dane z bufora, moze nie zapisac wszystkiego
        :param buffer: zrodlo danych
        :return: ilosc zapisanych bajtow
        """
        pass

    @abc.abstractmethod
    def write_all(self, buffer):
        """
        Zapisz dane z bufora w calosci
        :return: None
        """
        pass


class FileStreamProxy(StreamProxy):
    def __init__(self, infile: (str, pl.Path, tempfile.TemporaryFile), outdevice=None):
        self.at_exit = None

        if isinstance(infile, str):
            self._infile = open(infile, 'rb')
            self.at_exit = lambda: self._infile.close()
        elif isinstance(infile, pl.Path):
            self._infile = infile.open('rb')
            self.at_exit = lambda: self._infile.close()
        else:
            raise RuntimeError('Unsupported input file ({})'.format(repr(infile)))

        self._outdevice = outdevice

    def read(self, chunk_len: int):
        return self._infile.read(chunk_len)

    def write(self, buffer):
        return self._infile.write(buffer)

    def write_all(self, buffer):
        return self._infile.write_all(buffer)

    def seek0(self):
        return self._infile.seek(0)

    def __del__(self):
        if self.at_exit:
            self.at_exit()


class TempFileStreamProxy(StreamProxy):
    def __init__(self, infile, outfile):
        self._infile = infile
        self._outfile = outfile

    def read(self, chunk_len):
        return self._infile.read(chunk_len)

    def write(self, buffer):
        return self._outfile.write(buffer)

    def write_all(self, buffer):
        to_write = buffer[:]
        while to_write:
            written = self._outfile.write(to_write)
            to_write = to_write[written:]


class SocketStreamProxy(StreamProxy):
    def __init__(self, socket, timeout=None):
        self.socket = socket
        self.timeout = timeout

        if hasattr(socket, 'recv'):
            self.read_ = self.socket.recv
        else:
            self.read_ = self.socket.read

    # interestingly enough providing write as class member in init is not enough to satisfy "abstractness" of abc
    def read(self, chunk_size):
        return self.read_(chunk_size)

    def write(self, buffer):
        return self.socket.send(buffer)

    # TODO check if this socket has sendall
    def write_all(self, buffer):
        while buffer:
            sent = self.write(buffer)
            buffer = buffer[sent:]

    def set_timeout(self, value):
        self.socket.settimeout(value)


class ByteStream(StreamProxy):
    def __init__(self):
        self._buffer = bytearray()

    def read(self, chunk_size):
        result = self._buffer[:chunk_size]
        self._buffer = self._buffer[chunk_size:]
        return result

    def write(self, buffer):
        self._buffer += buffer
        return len(buffer)

    def write_all(self, buffer):
        self.write(buffer)
