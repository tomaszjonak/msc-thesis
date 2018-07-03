from ..utils import StreamTokenWriter, StreamTokenReader, PersistentQueue
import pathlib as pl
import logging
import time
import subprocess
import os
from sync import compressors

logger = logging.getLogger(__name__)


class ClientProtocolError(RuntimeError):
    pass


class ClientConfigurationError(RuntimeError):
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
    def __init__(self, reader, writer, stage_queue, storage_root, delete_acknowledged=False, **kwargs):
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
        self.transformation = None
        self.chunk_size = kwargs.get('chunk_size', 8192)
        self.cont = True
        self.queue_timeout = None
        self.delete_acknowledged = delete_acknowledged

        # zmienne maszyny stanow
        self.operation = self._send_metadata
        self.file_obj = None

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
        logger.debug('File transfer ended (took {} seconds)'.format(stop - start))

        self.operation = self._acknowledge_and_unstage

    def _acknowledge_and_unstage(self):
        logger.debug('_acknowledge_and_unstage')
        # TODO add some timeout
        ack_path = self.reader.get_token().decode()

        if ack_path == self.file_path:
            self.stage_queue.pop(pl.Path(ack_path).as_posix())
            logger.debug('Acknowledge received ({})'.format(str(ack_path)))
            if self.delete_acknowledged:
                logger.debug('Deleting acknowledged file ({})'.format(ack_path))
                self.file_obj.unlink()
        else:
            logger.error('Mismatched server acknowledge. Expected ({}, type {}), got ({}, type {})'
                         .format(self.file_path, type(self.file_path), ack_path, type(ack_path)))

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
    ffmpeg = os.environ.get("FFMPEG_PATH", "ffmpeg")

    compressors = {
        # 'wavelet': (compressors.wavelet.wavelet_lvm.encode_file, compressors.wavelet.map_extension),
        'x264': (compressors.x264.Compressor(ffmpeg), compressors.x264.map_extension),
        'bzip2': (compressors.bz2.compress, compressors.bz2.map_extension)
    }

    def __init__(self, *args, compression_settings, **kwargs):
        logger.info('CompressionEnabledSender::init (ffmpeg path: {})'.format(self.ffmpeg))

        self.verify_compression_settings(compression_settings)
        self.extension_map = compression_settings
        self.expected_ack_value = None
        logger.info('Keep in mind this implementation puts constraints on several file extensions ({})'
                    .format(self.extension_map.keys()))

        # TODO: add to settings

        super(CompressionEnabledSender, self).__init__(*args, **kwargs)

    def _send_metadata(self):
        logger.debug('_send_metadata')
        self.file_path = self.stage_queue.get(timeout=self.queue_timeout)
        self.file_obj = self.storage_root.joinpath(self.file_path)
        if not self.file_obj.exists():
            logger.error("File in queue does not exist on disk")
            self.stage_queue.pop(pl.Path(self.file_path).as_posix())
            return

        logger.info("Sending file ({})".format(self.file_path))
        self.operation = self._transfer_file

    def _transfer_file(self):
        logger.debug('_transfer_file')
        extension = self.file_obj.suffix.lstrip('.')

        try:
            compressor_tag = self.extension_map[extension]
            compressor, extension_mapper = self.compressors[compressor_tag]
        except KeyError:
            logger.debug('Null compression ({} file)'.format(extension))
            self.writer.write_token(self.file_path)
            self.expected_ack_value = self.file_path
            file_size = self.file_obj.stat().st_size
            self.writer.write_token(str(file_size))
            super(CompressionEnabledSender, self)._transfer_file()
            return
        except subprocess.CalledProcessError as e:
            logger.debug("Ffmpeg gave up, sending raw {}".format(e))
            super(CompressionEnabledSender, self)._transfer_file()
            return
        except Exception as e:
            logger.error("File transfer failed, giving up {}".format(e))

        try:
            compression_start = time.time()
            # TODO big enough file may exhaust memory
            compressed_bytes = compressor(self.file_obj)
            compression_end = time.time()
        except Exception as e:
            if self.file_obj.exists():
                logger.error("Compression failed, skipping file (exception: {}, file {})".format(e, self.file_path))
            else:
                logger.error("File from queue does not exist on disk (exception: {}, file {})".format(e, self.file_path))
            self.stage_queue.pop(pl.Path(self.file_path).as_posix())
            self.operation = self._send_metadata
            self.file_path = None
            self.file_obj = None
            self.expected_ack_value = None
        else:
            announced_file = str(self.file_obj
                                     .relative_to(self.storage_root)
                                     .with_suffix(extension_mapper(self.file_obj.suffix)))
            self.writer.write_token(announced_file)
            self.expected_ack_value = announced_file
            self.file_obj = self.storage_root.joinpath(self.file_path)

            logger.debug('Compression done ({} s)'.format(compression_end - compression_start))

            self.writer.write_token(str(len(compressed_bytes)))

            transfer_start = time.time()

            self.writer.write_bytes(compressed_bytes)

            transfer_end = time.time()
            logger.debug('File transfer done ({} s)'.format(transfer_end - transfer_start))

            self.writer.write_separator()

            self.operation = self._acknowledge_and_unstage

    def _acknowledge_and_unstage(self):
        logger.debug('_acknowledge_and_unstage')
        # TODO add some timeout
        ack_path = self.reader.get_token().decode()

        if ack_path == self.expected_ack_value:
            self.stage_queue.pop(pl.Path(self.file_path).as_posix())
            if self.delete_acknowledged:
                logger.debug('Deleting acknowledged file ({})'.format(ack_path))
                self.file_obj.unlink()
            logger.info("File sent ({})".format(str(ack_path)))
        else:
            logger.error('Mismatched server acknowledge. Expected ({}, type {}), got ({}, type {})'
                         .format(self.expected_ack_value, type(self.expected_ack_value), ack_path, type(ack_path)))

        self.file_path = None
        self.file_obj = None
        self.expected_ack_value = None
        self.operation = self._send_metadata

    @classmethod
    def verify_compression_settings(cls, settings):
        unknown = {compressor for compressor in settings.values()
                   if compressor and compressor not in cls.compressors.keys()}
        if unknown:
            raise ClientConfigurationError('Unsupported compressors specified ({})'.format(unknown))
