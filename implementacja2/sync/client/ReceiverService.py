from . import ReceiverProcessor
from ..utils import Workers
from ..utils import StreamProxy
from ..utils import StreamTokenReader
from ..utils import PersistentQueue


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
    def __init__(self, address, stage_queue, storage_root, **kwargs):
        if not isinstance(stage_queue, PersistentQueue.Queue):
            raise ReceiverServiceError('Unsupported queue type ({})'.format(repr(stage_queue)))

        self.thread = ReceiverThread(address, stage_queue, storage_root, **kwargs)
        self.thread.start()

    def is_running(self):
        return self.thread.isAlive()

    def stop(self):
        self.thread.stop()

    def __del__(self):
        if self.thread:
            self.thread.join()


class ReceiverThread(Workers.KeepAliveWorker):
    def __init__(self, address, stage_queue, storage_root, **kwargs):
        self.address = address
        self.queue = stage_queue
        self.storage_root = storage_root

        self.separator = kwargs.get('separator', '\n')
        self.extensions = kwargs.get('extensions', ['lvm', 'avi'])
        retry_time = kwargs.get('retry_time', 30)
        super(ReceiverThread, self).__init__(address, retry_time)

    def work(self):
        processor = self._prepare_processor()
        try:
            processor.run()
        except StreamTokenReader.StreamTokenReaderError as e:
            print('Stream error, restarting connection ({})'.format(e))

    def _prepare_processor(self):
        stream = StreamProxy.SocketStreamProxy(self.socket)
        reader = StreamTokenReader.StreamTokenReader(stream, self.separator)
        return ReceiverProcessor.ReceiverProcessor(reader, self.queue, self.storage_root, self.extensions)

    def stop(self):
        super(ReceiverThread, self).stop()
