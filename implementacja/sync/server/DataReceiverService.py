import pathlib as pl
import threading
import socketserver
import logging
import socket

from ..utils import StreamProxy
from ..utils import StreamTokenReader
from ..utils import StreamTokenWriter
from . import ServerProtocolProcessor as proc


logger = logging.getLogger(__name__)


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

    def __init__(self, address, storage_root, **kwargs):
        self.options = kwargs
        self.address = address
        if isinstance(storage_root, str):
            self.storage_root = pl.Path(storage_root)
        elif isinstance(storage_root, pl.Path):
            self.storage_root = storage_root
        else:
            raise RuntimeError('Invalid storage root provided ({})'.format(repr(storage_root)))

        self.storage_root.mkdir(exist_ok=True, parents=True)

        self.thread = DataReceiverThread(address, storage_root)
        self.thread.start()

    def is_running(self):
        return self.thread.isAlive()

    def stop(self):
        self.thread.stop()

    def __del__(self):
        if self.thread.isAlive():
            self.thread.join()


class DataReceiverThread(threading.Thread):
    def __init__(self, address, storage_root):
        self.address = address
        self.storage_root = storage_root
        super(DataReceiverThread, self).__init__()
        self.name = 'DataReceiverThread'
        self.server = DataReceiverServer(self.address, DataReceiverHandler, self.storage_root)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class DataReceiverServer(socketserver.TCPServer, socketserver.ThreadingMixIn):
    def __init__(self, address, handler_cls, storage_root, decompression_settings, **kwargs):
        self.options = kwargs
        self.storage_root = storage_root
        self.cont = True
        self.allow_reuse_address = True
        self.decompression_settings = decompression_settings
        super(DataReceiverServer, self).__init__(address, handler_cls)

    def shutdown(self):
        self.cont = False
        super(DataReceiverServer, self).shutdown()


class DataReceiverHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.storage_root = self.server.storage_root
        self.decompression_settings = self.server.decompression_settings

    def handle(self):
        logger.info('Connection from {}'.format(self.client_address))
        processor = self.prepare_processor(self.request, self.storage_root, self.decompression_settings)
        try:
            processor.run()
        except Exception as e:
            # we have some connection breaking condition, just stop handling
            logger.exception(e)

    @staticmethod
    def prepare_processor(socket: socket.socket, storage_root, decompression_settings):
        # 5 minutes timeout
        socket.settimeout(5*60)
        stream = StreamProxy.SocketStreamProxy(socket)
        # TODO czy ustawic konfigurowalny separator?
        reader = StreamTokenReader.StreamTokenReader(stream, b'\r\n')
        writer = StreamTokenWriter.StreamTokenWriter(stream, b'\r\n')

        return proc.ServerDecompressionProcessor(reader=reader, writer=writer, storage_root=storage_root,
                                                 decompression_settings=decompression_settings)
