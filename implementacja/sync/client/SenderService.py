from ..utils import Workers
from ..utils import StreamTokenReader
from ..utils import StreamTokenWriter
from ..utils import StreamProxy
from . import SenderProtocolProcessor as spp
import logging

logger = logging.getLogger(__name__)


class SenderServiceException(Exception):
    pass


class SenderService(object):
    """
    Serwis odpowiedzialny za komunikacje (uzywajac okreslonego protokolu) z serwerem

    Schemat dzialania:
    1.  Nawiazanie polaczenia z serwerem
    2.  Odebranie informacji o najnowszym pliku zapisanym na serwerze (patrz pojecia)
    3.  (opcjonalne) uzupelnienie koljeki o pliki ktore zostaly stworzone ale nie rozgloszone (synchronizacja)
    4.  Pobieranie plikow z kolejki
    4.5 (opcjonalne) kompresja pliku
    5.  Przesyl zgodnie z zadanym protokolem
    6.  Usuniecie plikow z kolejki po otrzymaniu potwierdzenia zapisania przez serwer

    Pojecia:
    Najnowszy plik zapisany na serwerze - porzadek plikow ustala data zawarta w nazwie pliku
    Synchronizacja - obsluzenie nieplanowanego bledu w dzialaniu ktoregos z komponentow

    Dodatkowe informacje:
    * Serwis ponawia polaczenie analogicznie do odbierajcego z labview
    * Schemat kompresji jest wymienny, istnieje mozliwosc wyboru schematu kompresji w zaleznosci od rozszerzenia pliku
    """
    def __init__(self, address, storage_root, stage_queue, compression_settings, **kwargs):
        self.address = address
        self.storage_root = storage_root
        self.stage_queue = stage_queue
        self.thread = SenderThread(address, storage_root, stage_queue, compression_settings, **kwargs)
        self.thread.start()

    def is_alive(self):
        return self.thread.isAlive()

    def stop(self):
        self.thread.stop()

    def __del__(self):
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()


class SenderThread(Workers.KeepAliveWorker):
    supported_processors = {
        'basic': spp.SenderProtocolProcessor,
        'compression': spp.CompressionEnabledSender
    }

    def __init__(self, address, storage_root, stage_queue, compression_settings, **kwargs):
        self.storage_root = storage_root
        self.stage_queue = stage_queue
        self.processor = None
        self.delete_acknowledged = kwargs.get('delete_acknowledged', False)
        spp.CompressionEnabledSender.verify_compression_settings(compression_settings)
        self.compression_settings = compression_settings

        self.separator = kwargs.get('separator', b'\r\n')
        retry_time = kwargs.get('retry_time', 30)
        super(SenderThread, self).__init__(address, retry_time)
        self.name = 'SenderThread'

    def work(self):
        self.processor = self._prepare_processor()
        try:
            self.processor.run()
        except StreamTokenReader.StreamTokenReaderError as e:
            logger.exception(e)
            raise e
        except TimeoutError:
            pass

    def _prepare_processor(self):
        stream = StreamProxy.SocketStreamProxy(self.socket)
        reader = StreamTokenReader.StreamTokenReader(stream, self.separator)
        writer = StreamTokenWriter.StreamTokenWriter(stream, self.separator)

        proc = spp.CompressionEnabledSender(
            reader=reader,
            writer=writer,
            storage_root=self.storage_root,
            stage_queue=self.stage_queue,
            delete_acknowledged=self.delete_acknowledged,
            compression_settings=self.compression_settings
        )

        return proc

    def stop(self):
        if self.processor:
            self.processor.stop()
        super(SenderThread, self).stop()
