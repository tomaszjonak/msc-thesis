import abc
import pathlib as pl


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
    def __init__(self, infile: (str, pl.Path), outdevice=None):
        if isinstance(infile, str):
            self._infile = open(infile, 'rb')
            self.at_exit = lambda: self._infile.close()
        elif isinstance(infile, pl.Path):
            self._infile = infile.open('rb')
            self.at_exit = lambda: self._infile.close()
        else:
            raise RuntimeError('Unsupported input file ({})'.format(repr(infile)))

        self._outdevice = outdevice
        self.at_exit = None

    def read(self, chunk_len: int):
        return self._infile.read(chunk_len)

    def write(self, buffer):
        pass

    def write_all(self, buffer):
        pass

    def __del__(self):
        if self.at_exit:
            self.at_exit()
