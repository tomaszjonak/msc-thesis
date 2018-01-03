from ..utils import StreamTokenWriter, StreamTokenReader, FilesystemHelpers
from sync import compressors

import pathlib as pl
import numpy as np
import logging


logger = logging.getLogger(__name__)


class ServerConfigurationError(RuntimeError):
    pass


class ServerProtocolProcessor(object):
    """
    Klasa odpowiedzialna za przetwarzanie danych przychodzacych ze strumienia zgodnie
    z protokolem zdefiniowanym w trakcie pracy.

    Klasa nie jest odpowiedzialna za szeroko pojete nawiazywanie/utrzymywanie polaczen (tworzenie strumieni)
    oraz obsluge bledow z nimi zwiazanych.
    """
    def __init__(self, reader: StreamTokenReader.StreamTokenReader, writer: StreamTokenWriter.StreamTokenWriter,
                 storage_root: (str, pl.Path), **kwargs):
        if not isinstance(reader, StreamTokenReader.StreamTokenReader):
            raise RuntimeError('Unsupported reader type')
        if not isinstance(writer, StreamTokenWriter.StreamTokenWriter):
            raise RuntimeError('Unsupported writer type')

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

        self.cont = True
        self.queue_timeout = None

        self.options = kwargs

        self._file_description = {
            'filename': None,
            'file_pathobj': None,
            'size': None
        }

        self.operation = self._process_filename

    def _process_filename(self):
        """
        Pobiera ze streamu pierwszy token, sprawdza czy jest poprawna sciezka systemowa
        """
        filename = self.reader.get_token().decode('utf8')
        if not filename:
            return
        logger.info('Receiving file ({})'.format(filename))

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
            for i in range(full_chunks):
                FilesystemHelpers.write_all(fd, self.reader.get_bytes(chunk_size))
            if last_chunk_size:
                FilesystemHelpers.write_all(fd, self.reader.get_bytes(last_chunk_size))

        self.operation = self._announce_response

    def _announce_response(self):
        """
        Potwierdzenie odebrania pliku przez serwer, domyka transakcje
        """
        path = self._file_description['filename']
        logger.info('Announcing back ({})'.format(path))
        self.writer.write_token(path)

        self.operation = self._process_filename

    def run(self):
        while self.cont:
            self.operation()

    def stop(self):
        self.cont = False
        self.reader.timeout = 1


class ServerDecompressionProcessor(ServerProtocolProcessor):
    decompressors = {
        'wavelet': (compressors.wavelet.wavelet_lvm.decode_to_bytestream, compressors.wavelet.remap_extension),
        'bzip2': (compressors.bz2.decompress, compressors.bz2.remap_extension)
    }
    fmt = '%.6f'
    delimiter = '\t'

    def __init__(self, reader: StreamTokenReader.StreamTokenReader, writer: StreamTokenWriter.StreamTokenWriter,
                 storage_root: (str, pl.Path), decompression_settings, **kwargs):
        super(ServerDecompressionProcessor, self).__init__(reader, writer, storage_root, **kwargs)
        self.verify_decompression_settings(decompression_settings)
        self.extension_map = decompression_settings

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
        buffer = bytearray()
        for _ in range(full_chunks):
            buffer += self.reader.get_bytes(chunk_size)
        buffer += self.reader.get_bytes(last_chunk_size)

        suffix = path.suffixes[0].lstrip('.')

        self.operation = self._announce_response

        try:
            decompressor_id = self.extension_map[suffix]
            decompressor, suffix_mapper = self.decompressors[decompressor_id]
            data = decompressor(buffer)
        except KeyError:
            logger.debug('No decompression scheme associated with extension, dumping raw to disk ({})'.format(suffix))
            path.write_bytes(buffer)
            return
        except Exception as e:
            logger.exception(e)
            logger.debug('Decompression failed for given file, saving raw representation')
            self.save_failed_file(buffer)
            return

        dest_path = path.with_name(path.name.split('.')[0]).with_suffix(suffix_mapper(path.suffixes))
        dest_path.write_bytes(data)

        # TODO currently its easy to just assume its lvm here, change to generic handling
        # np.savetxt(str(path), data, fmt=self.fmt, delimiter=self.delimiter)

    def save_failed_file(self, buffer):
        name = self._file_description['filename']
        error_loc = self.storage_root.joinpath('failed_decompression')
        file_path = error_loc.joinpath(name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(buffer)

    @classmethod
    def verify_decompression_settings(cls, settings):
        unknown = {compressor for compressor in settings.values()
                   if compressor and compressor not in cls.decompressors.keys()}
        if unknown:
            raise ServerConfigurationError('Unsupported compressors specified ({})'.format(unknown))
