import pathlib as pl
import threading
import socketserver

from ..utils import PersistentQueue
from ..utils import StreamProxy
from ..utils import StreamTokenReader
from ..utils import StreamTokenWriter
from . import ServerProtocolProcessor as proc


class DataReceiverService(object):
    """
    Serwis odpowiedzialny za odbior plikow od klienta, weryfikacje integralnosci plikow oraz zapisanie
    danych na zadanym nosniku (dysku twardym serwera).

    Schemat dzialania:
    1.  Oczekiwanie na polaczenie
    2.  Wyslanie informacji o najnowszym pliku
    3.  Odebranie pliku wedlug zadanego protokolu
    3.5 (opcjonalnie) dekompresja
    4.  Zapisanie pliku na nosniku
    5.  Wyslanie potwierdzenia do klienta

    Informacje dodatkowe
    * Informacja o najnowszym pliku musi byc odporna na nagle przerwanie dzialania programu
      w praktyce uniemozliwia to trzymanie jej w ramie, musi to byc jakas forma pamieci trwalej (np. dysk twardy)
    """

    def __init__(self, address, storage_root, cache=None, **kwargs):
        self.options = kwargs
        self.address = address
        if isinstance(storage_root, str):
            self.storage_root = pl.Path(storage_root)
        elif isinstance(storage_root, pl.Path):
            self.storage_root = storage_root
        else:
            raise RuntimeError('Invalid storage root provided ({})'.format(repr(storage_root)))

        self.storage_root.mkdir(exist_ok=True, parents=True)
        self.cache = cache or PersistentQueue.SqliteQueue(kwargs.get('cache_file', 'cache.db'))

        self.thread = DataReceiverThread(address, cache, storage_root)
        self.thread.start()

    def is_running(self):
        return self.thread.isAlive()

    def stop(self):
        self.thread.stop()

    def __del__(self):
        if self.thread.isAlive():
            self.thread.join()


class DataReceiverThread(threading.Thread):
    def __init__(self, address, cache, storage_root):
        self.address = address
        self.cache = cache
        self.storage_root = storage_root
        super(DataReceiverThread, self).__init__()
        self.name = 'DataReceiverThread'
        self.server = DataReceiverServer(self.address, DataReceiverHandler, self.cache, self.storage_root)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class DataReceiverServer(socketserver.TCPServer, socketserver.ThreadingMixIn):
    def __init__(self, address, handler_cls, cache, storage_root, **kwargs):
        self.cache = cache
        self.options = kwargs
        self.storage_root = storage_root
        self.cont = True
        self.allow_reuse_address = True
        super(DataReceiverServer, self).__init__(address, handler_cls)

    def shutdown(self):
        self.cont = False
        super(DataReceiverServer, self).shutdown()


class DataReceiverHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.cache = self.server.cache
        self.storage_root = self.server.storage_root

    def handle(self):
        processor = self.prepare_processor(self.request, self.cache, self.storage_root)
        try:
            processor.run()
        except Exception as e:
            # we have some connection breaking condition, just stop handling
            print(repr(e))

    @staticmethod
    def prepare_processor(socket, cache, storage_root):
        stream = StreamProxy.SocketStreamProxy(socket)
        # TODO czy ustawic konfigurowalny separator?
        reader = StreamTokenReader.StreamTokenReader(stream, b'\r\n')
        writer = StreamTokenWriter.StreamTokenWriter(stream, b'\r\n')

        return proc.ServerProtocolProcessor(reader=reader, writer=writer,
                                            disk_cache=cache, storage_root=storage_root)
