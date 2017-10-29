from ..utils import StreamTokenWriter, StreamTokenReader, PersistentQueue
import pathlib as pl


class ServerProtocolProcessor(object):
    """
    Klasa odpowiedzialna za przetwarzanie danych przychodzacych ze strumienia zgodnie
    z protokolem zdefiniowanym w trakcie pracy.

    Klasa nie jest odpowiedzialna za szeroko pojete nawiazywanie/utrzymywanie polaczen (tworzenie strumieni)
    oraz obsluge bledow z nimi zwiazanych.
    """
    def __init__(self, reader: StreamTokenReader.StreamTokenReader, writer: StreamTokenWriter.StreamTokenWriter,
                 disk_cache: PersistentQueue.Queue):
        if not isinstance(reader, StreamTokenReader.StreamTokenReader):
            raise RuntimeError('Unsupported reader type')
        if not isinstance(writer, StreamTokenWriter.StreamTokenWriter):
            raise RuntimeError('Unsupported writer type')
        if not isinstance(disk_cache, PersistentQueue.Queue):
            raise RuntimeError('Unsupported disk cache type')

        self.reader = reader
        self.writer = writer
        self.cache = disk_cache
        self._file_description = {
            'filename': None,
            'file_pathobj': None,
            'size': None,
            'fd': None
        }

        self.operation = self._send_cached_filename

    def _send_cached_filename(self):
        newest_file = self.cache.get(wait_for_value=False)
        self.writer.write_token(newest_file)

        self.operation = self._process_filename

    def _process_filename(self):
        filename = self.reader.get_token().decode('utf8')
        if not filename:
            return
        path = pl.Path(filename)
        if any(len(part) > 255 for part in path.parts):
            # TODO: log some message?
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
        raise RuntimeError('implement that')

    def run(self):
        while True:
            self.operation()
