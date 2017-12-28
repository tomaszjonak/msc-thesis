from ..utils import StreamTokenWriter, StreamTokenReader, PersistentQueue
from ..wavelet_compression import wavelet_lvm
import pathlib as pl
import logging
import time

logger = logging.getLogger(__name__)


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
    def __init__(self, reader, writer, stage_queue, storage_root, sync_queue=None, **kwargs):
        logger.debug('SenderProtocolProcessor::init')
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

        if not (self.storage_root.exists() or self.storage_root.is_dir()):
            raise ClientProtocolError("Storage root has to be directory")

        self.reader = reader
        self.writer = writer
        self.stage_queue = stage_queue
        self.sync_queue = sync_queue
        self.transformation = None
        self.chunk_size = kwargs.get('chunk_size', 8192)
        self.cont = True
        self.queue_timeout = None

        # zmienne maszyny stanow
        self.operation = self._receive_last_valid
        self.file_obj = None

    def _receive_last_valid(self):
        logger.debug('_receive_last_valid')
        last_on_server = self.reader.get_token().decode()
        logger.debug('Received last file from server ({})'.format(last_on_server))
        # technically there should be some check, we might encounter situation where
        # last valid file gets archieved by cron job and thus path is no longer usable
        # last_path = self.storage_root.joinpath(last_on_server)
        # stage_snapshot = self.stage_queue.get_all()
        # self.sync_queue.put((last_path, stage_snapshot))

        self.operation = self._send_metadata

    def _send_metadata(self):
        logger.debug('_send_metadata')
        self.file_path = self.stage_queue.get(timeout=self.queue_timeout)
        self.writer.write_token(self.file_path)

        self.file_obj = self.storage_root.joinpath(self.file_path)
        file_size = self.file_obj.stat().st_size
        self.writer.write_token(str(file_size))

        self.operation = self._transfer_file

    def _transfer_file(self):
        logger.debug('_transfer_file')
        start = time.time()
        # bts = 0
        with self.file_obj.open('rb') as fd:
            data_chunk = fd.read(self.chunk_size)
            while data_chunk:
                self.writer.write_bytes(data_chunk)
                # bts += len(data_chunk)
                # logger.debug('Sent {} bytes'.format(bts))
                data_chunk = fd.read(self.chunk_size)
        self.writer.write_separator()
        stop = time.time()
        logger.debug('File transfer took ended (took {} seconds)'.format(stop - start))

        self.operation = self._acknowledge_and_unstage

    def _acknowledge_and_unstage(self):
        logger.debug('_acknowledge_and_unstage')
        # TODO add some timeout
        ack_path = self.reader.get_token().decode()

        if ack_path == self.file_path:
            self.stage_queue.pop(pl.Path(ack_path).as_posix())
            logger.debug('Acknowledge received ({})'.format(str(ack_path)))
        else:
            logger.error('Mismatched server acknowledge. Expected ({}), got ({})'
                         .format(self.file_path, ack_path))

        self.file_path = None
        self.file_obj = None
        self.operation = self._send_metadata

    def run(self):
        while self.cont:
            try:
                self.operation()
            except (StreamTokenReader.StreamTokenReaderError, BrokenPipeError, ConnectionResetError):
                raise
            except Exception as e:
                logger.error('Exception in event loop')
                logger.exception(e)

    def stop(self):
        self.reader.timeout = 1
        self.cont = False
        self.queue_timeout = 1


class CompressionEnabledSender(SenderProtocolProcessor):
    compressors = {'lvm': wavelet_lvm.encode_file}

    def __init__(self, reader, writer, stage_queue, storage_root, sync_queue):
        logger.info('CompressionEnabledSender::init')
        logger.info('Keep in mind this implementation puts constraints on several file extensions ({})'
                    .format(self.compressors.keys()))
        super(CompressionEnabledSender, self).__init__(reader, writer, stage_queue, storage_root, sync_queue)

    def _send_metadata(self):
        logger.debug('_send_metadata')
        self.file_path = self.stage_queue.get(timeout=self.queue_timeout)
        self.writer.write_token(self.file_path)

        self.file_obj = self.storage_root.joinpath(self.file_path)

        self.operation = self._transfer_file

    def _transfer_file(self):
        logger.debug('_transfer_file')
        extension = self.file_obj.suffix.lstrip('.')

        try:
            compression_begin = time.time()
            blob = self.compressors[extension](str(self.file_obj))

            self.writer.write_token(str(len(blob)))
            compression_end = time.time()
            logger.debug('Compression done ({} s)'.format(compression_end - compression_begin))
        except KeyError:
            file_size = self.file_obj.stat().st_size
            self.writer.write_token(str(file_size))
            logger.debug('No compression scheme for extension ({})'.format(extension))
            super(CompressionEnabledSender, self)._transfer_file()
            return

        transfer_start = time.time()
        self.writer.write_bytes(blob)
        transfer_end = time.time()
        logger.debug('Transfer done ({} s)'.format(transfer_end - transfer_start))
        self.writer.write_separator()

        self.operation = self._acknowledge_and_unstage
