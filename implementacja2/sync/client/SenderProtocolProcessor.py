from ..utils import StreamTokenWriter, StreamTokenReader, PersistentQueue
import pathlib as pl


class ClientProtocolError(RuntimeError):
    pass


class SenderProtocolProcessor(object):
    """
    Klasa odpowiedzialna za obsluge komunikacji (strumienia danych) zestawionego z serwerem.
    Bezposrednio odpowiada za przeslanie plikow.

    Zalozenia:
    * Do kolejki trafiaja tylko faktycznie istniejace pliki (receiver service jest odpowiedzialny za walidacje).
    * Przy zerwaniu polaczenia tworzony jest nowy bufor tcp, nie ma mozliwosci aby przy starcie
      znajdowaly sie w nim nieporzadane dane.
    * Jedynym zadaniem dodatkowym obslugiwanym przez ten serwis
      jest przeprowadzenie transformacji (i.e kompresja przed wyslaniem)
    """
    def __init__(self, reader, writer, stage_queue, storage_root, **kwargs):
        if not isinstance(reader, StreamTokenReader.StreamTokenReader):
            raise RuntimeError('Unsupported reader type')
        if not isinstance(writer, StreamTokenWriter.StreamTokenWriter):
            raise RuntimeError('Unsupported writer type')
        if not isinstance(stage_queue, PersistentQueue.Queue):
            raise RuntimeError('Unsupported queue type')

        # lokalizacja na dysku relatywnie do ktorej podawane sa pliki
        # przez labview
        if isinstance(storage_root, str):
            self.storage_root = pl.Path(storage_root)
        elif isinstance(storage_root, pl.Path):
            self.storage_root = storage_root
        else:
            raise ClientProtocolError("Unsupported storage_root type ({})".format(storage_root))

        # TODO sprawdzic czy storage root istnieje
        if not (self.storage_root.exists() or self.storage_root.is_dir()):
            raise ClientProtocolError("Storage root has to be directory")

        self.reader = reader
        self.writer = writer
        self.stage_queue = stage_queue
        self.transformation = None
        self.chunk_size = kwargs.get('chunk_size', 8192)

        # zmienne maszyny stanow
        self.operation = self._receive_last_valid
        self.file_obj = None

    def _receive_last_valid(self):
        last_on_server = self.reader.get_token()
        # sync_queue.put('last_on_server')

        self.operation = self._send_metadata

    def _send_metadata(self):
        self.file_path = self.stage_queue.get()
        self.writer.write_token(self.file_path)

        self.file_obj = self.storage_root.joinpath(self.file_path)
        file_size = self.file_obj.stat().st_size
        self.writer.write_token(str(file_size))

        self.operation = self._transfer_file

    def _transfer_file(self):
        with self.file_obj.open('rb') as fd:
            data_chunk = fd.read(self.chunk_size)
            while data_chunk:
                self.writer.write_bytes(data_chunk)
                data_chunk = fd.read(self.chunk_size)
        self.writer.write_separator()

        self.operation = self._acknowledge_and_unstage

    def _acknowledge_and_unstage(self):
        # TODO add some timeout
        ack_path = self.reader.get_token().decode()

        if ack_path == self.file_path:
            self.stage_queue.pop(self.file_path)
        else:
            print('Server acknowledge error. Expected ({}), got ({})'
                  .format(self.file_path, ack_path))

        self.file_path = None
        self.file_obj = None

        self.operation = self._send_metadata

    def run(self):
        while True:
            self.operation()
