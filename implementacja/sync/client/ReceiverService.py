from . import ReceiverProcessor
from ..utils import Workers
from ..utils import StreamProxy
from ..utils import StreamTokenReader
from ..utils import PersistentQueue

import logging
logger = logging.getLogger(__name__)


class ReceiverServiceError(RuntimeError):
    pass


class ReceiverService(object):
    """
    Serwis odpowiedzialny za odbieranie danych o nowopowstalych plikach od providera.

    Schemat dzialania:
    1. Proba polaczenia z socketem wystawionym przez druga strone
    2. Odbieranie danych z bufora tcp (tzw. strumienia)
    3. Rozdzielanie danych ze strumienia
    4. Zweryfikowanie istnienia plikow na podstawie skonfigurowanych rozszerzen
    5. Dodanie plikow do kolejki

    Pojecia:
    Staged/Announced file - plik "ogloszony" przez labview oraz faktycznie istniejacy na dysku
                            ktory nie zostal jeszcze zapisany na serwerze. W praktyce kazdy plik w kolejce.
    Provider - program obslugujacy stanowisko pomiarowe, rozglaszajacy stworzone pliki z pomiarami.
               Pliki rozglaszane sa poprzez socket (tcp) o zadanym adresie.

    Informacje dodatkowe:
    * Po zerwaniu polaczenia przez druga strone serwis wykonuje proby ponownego nawiazania co okreslony interwal
    * Kolejka musi byc w stanie przechowac swoj stan w przypadku naglego zakonczenia
      dzialania programu (np. odciecie zasilania)
    """
    def __init__(self, address, stage_queue, storage_root, cache, sync_queue=None, avi_queue=None, **kwargs):
        if not isinstance(stage_queue, PersistentQueue.Queue):
            raise ReceiverServiceError('Unsupported queue type ({})'.format(repr(stage_queue)))

        self.thread = ReceiverThread(address, stage_queue, storage_root, cache,
                                     sync_queue=sync_queue, avi_queue=avi_queue, **kwargs)
        logger.info('Starting receiver service')
        self.thread.start()

    def is_running(self):
        return self.thread.isAlive()

    def stop(self):
        logger.info('Stopping receiver service')
        self.thread.stop()

    def __del__(self):
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()


class ReceiverThread(Workers.KeepAliveWorker):
    def __init__(self, address, stage_queue, storage_root, cache,
                 sync_queue=None, avi_queue=None, **kwargs):
        self.address = address
        self.queue = stage_queue
        self.storage_root = storage_root
        self.cache = cache
        self.avi_queue = avi_queue

        self.sync_queue = sync_queue
        self.processor = None
        self.separator = kwargs.get('separator', '\n')
        self.extensions = kwargs.get('extensions', ['lvm', 'avi'])
        retry_time = kwargs.get('retry_time', 30)
        super(ReceiverThread, self).__init__(address, retry_time)
        self.name = 'ReceiverThread'

    def work(self):
        self.processor = self._prepare_processor()
        try:
            self.processor.run()
        except StreamTokenReader.StreamTokenReaderError as e:
            logger.info('Stream error, restarting connection ({})'.format(e))
            raise

    def _prepare_processor(self):
        stream = StreamProxy.SocketStreamProxy(self.socket)
        reader = StreamTokenReader.StreamTokenReader(stream, self.separator)
        proc = ReceiverProcessor.ReceiverProcessor(
            reader=reader,
            queue=self.queue,
            storage_root=self.storage_root,
            supported_extensions=self.extensions,
            sync_queue=self.sync_queue,
            avi_queue=self.avi_queue,
            cache=self.cache
        )
        return proc

    def stop(self):
        if self.processor:
            self.processor.stop()
        super(ReceiverThread, self).stop()
