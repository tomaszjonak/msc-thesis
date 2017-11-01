from ..utils import StreamTokenWriter, StreamTokenReader, PersistentQueue, FilesystemHelpers
import pathlib as pl
import datetime as dt


class ServerProtocolProcessor(object):
    """
    Klasa odpowiedzialna za przetwarzanie danych przychodzacych ze strumienia zgodnie
    z protokolem zdefiniowanym w trakcie pracy.

    Klasa nie jest odpowiedzialna za szeroko pojete nawiazywanie/utrzymywanie polaczen (tworzenie strumieni)
    oraz obsluge bledow z nimi zwiazanych.
    """
    def __init__(self, reader: StreamTokenReader.StreamTokenReader, writer: StreamTokenWriter.StreamTokenWriter,
                 disk_cache: PersistentQueue.Queue, storage_root: (str, pl.Path), **kwargs):
        if not isinstance(reader, StreamTokenReader.StreamTokenReader):
            raise RuntimeError('Unsupported reader type')
        if not isinstance(writer, StreamTokenWriter.StreamTokenWriter):
            raise RuntimeError('Unsupported writer type')
        if not isinstance(disk_cache, PersistentQueue.Queue):
            raise RuntimeError('Unsupported disk cache type')

        # lokacja na dysku w ktorej skladowane beda pliki
        # wszystkie sciezki przeslane przez klienta
        if isinstance(storage_root, str):
            self.storage_root = pl.Path(storage_root)
        elif isinstance(storage_root, pl.Path):
            self.storage_root = storage_root
        else:
            raise RuntimeError('Unsupported storage_root type ({})'.format(repr(storage_root)))

        self.reader = reader
        self.writer = writer
        self.cache = disk_cache

        self.options = kwargs

        self._file_description = {
            'filename': None,
            'file_pathobj': None,
            'size': None
        }

        self.operation = self._send_cached_filename

    def _send_cached_filename(self):
        """
        (Synchronizacja) przesyl informacji o ostatnim wygenerowanym przez labview pliku
        ktory zostal poprawnie zapisany na serwerze.
        """
        newest_file = self.cache.get(wait_for_value=False)
        self.writer.write_token(newest_file)

        self.operation = self._process_filename

    def _process_filename(self):
        """
        Pobiera ze streamu pierwszy token, sprawdza czy jest poprawna sciezka systemowa
        """
        filename = self.reader.get_token().decode('utf8')
        if not filename:
            return

        path = self.storage_root.joinpath(filename)
        if any(len(part) > 255 for part in path.parts):
            # TODO: log some message? skip to next token?
            return

        self._file_description['filename'] = filename
        self._file_description['file_pathobj'] = path

        self.operation = self._process_file_length

    def _process_file_length(self):
        file_len = self.reader.get_token().decode('utf8')
        length = int(file_len)
        self._file_description['size'] = length

        self.operation = self._process_file_bytes

    def _process_file_bytes(self):
        """
        Sekwencja odpowiedzialna za faktyczne odebranie pliku
        TODO: checksuma
        """
        path = self._file_description['file_pathobj']
        path.parent.mkdir(exist_ok=True, parents=True)
        chunk_size = self.options.get('chunk_size', 8192)

        size = self._file_description['size']
        full_chunks = size // chunk_size
        last_chunk_size = size % chunk_size
        with path.open('wb') as fd:
            for _ in range(full_chunks):
                chunk = self.reader.get_bytes(chunk_size)
                fd.writeall(chunk)
            # so much for high level interfaces, this write has to be done c style
            # fd.writeall(self.reader.get_bytes(last_chunk_size))
            FilesystemHelpers.write_all(fd, self.reader.get_bytes(last_chunk_size))

        self.operation = self._announce_response

    def _announce_response(self):
        """
        Potwierdzenie odebrania pliku przez serwer, domyka transakcje
        """
        path = self._file_description['filename']
        self.writer.write_token(path)

        self.operation = self._update_cache

    def newer_file(self, left, right):
        """
        Czynnosc potrzebna klientowi w momencie wygenerowania plikow przez labview przed 'wstaniem'
        sync clienta. Przekazuje informacje o najswiezszym odebranym pliku (co do daty wygenerowania przez labview)
        :param left: str - sciezka do lewego pliku (pathlike)
        :param right: str - sciezka do prawego pliku (pathlike)
        :return: bool - czy lewy jest nowszy od prawego
        """
        time_formatstr = self.options.get('formatstr', 'M%y%m%d-%H%M%S')

        left_date = dt.datetime.strptime(left, time_formatstr)
        right_date = dt.datetime.strptime(right, time_formatstr)
        return left_date > right_date

    def _update_cache(self):
        """
        Sprawdza zawartosc dyskowego cache, podmienia wartosc jesli jest nowsza
        """
        last_element = self.cache.get(wait_for_value=False)
        current_element = self._file_description['filename']

        if not last_element:
            self.cache.put(current_element)
        else:
            last_path = pl.Path(last_element)
            curr_path = pl.Path(current_element)
            if self.newer_file(curr_path.name, last_path.name):
                self.cache.pop(last_element)
                self.cache.put(current_element)

        # For testing purposes, this should always have one entry
        assert self.cache.len() == 1

        self.operation = self._process_filename

    def run(self):
        while True:
            self.operation()
