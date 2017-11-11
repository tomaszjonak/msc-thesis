import threading
from . import SyncProcessor


class SynchronizationService(object):
    """
    Klasa umozliwiajaca zarzadzanie watkiem synchronizacyjnym (glownie zatrzymanie)
    """
    def __init__(self, stage_queue, client_queue, server_queue, storage_root, **kwargs):
        self.stage_queue = stage_queue
        self.client_queue = client_queue
        self.server_queue = server_queue
        self.storage_root = storage_root

        self.extensions = kwargs.get('extensions', ['lvm', 'avi'])

        self.thread = SynchronizationThread(
            server_queue=self.server_queue,
            client_queue=self.client_queue,
            queue_view=self.stage_queue,
            storage_root=self.storage_root,
            extensions=self.extensions
        )
        self.thread.start()

    def is_running(self):
        self.thread.isAlive()

    def stop(self):
        self.thread.stop()

    def __del__(self):
        if self.thread.isAlive():
            self.thread.join()


class SynchronizationThread(threading.Thread):
    """
    Implementacja logiki odpowiedzialnej za synchronizacje stanow
    po bledzie.

    Do poprawnego przeprowadzenia synchronizacji potrzbene sa dwie informacje:
    - ostatni poprawnie zapisany na serwerze plik
    - pierwszy plik przyslany przez labview w obecnej sesji
    W praktyce potrzebne sa czasy stworzenia obu tych plikow po stronie klienta.

    Zakladamy ze nie ma mozliwosci aby plik z pomiarami nagrany pozniej w rozumieniu
    czasu rzeczywistego zostal stworzony wczesniej niz go poprzedzajacy.
    Brak spelnienia takiego kontraktu doprowadzi do bledow w dzialaniu oprogramowania.

    Powyzsze informacje przychodza z dwoch zrodel:
    ostatni poprawny   - serwis odpowiedzialny za komunikacje z serwerem
    pierwszy nowy      - serwis odbierajacy dane z oprogramowania pomiarowego

    Do ich odbioru wymagany jest mechanizm synchronizacyjny ktory uspi ten watek
    do czasu pobrania obu informacji

    W obecnej implementacji wykozystano kolejki zamiast muteksow, poniewaz nie wymagaja
    przekazywania zarowno obiektu synchronizujacego jak i samego zasobu.

    Wykorzystanie kolejek wprowadza ryzyko, ze uzyta zostanie niepoprawnie zestawiona para.
    Co oznacza ze dla sesji Sn (Cn, Sn) oraz Sm (Cm, Sm) zamiast oczekiwanego zestawu informacji
    Cn Sn synchronizacja zostanie przeprowadzona dla pary (Cn, Sm) co nie ma wiekszego sensu.
    """
    def __init__(self, server_queue, client_queue, queue_view, storage_root, extensions):
        self.server_queue = server_queue
        self.client_queue = client_queue
        self.stage_queue = queue_view
        self.storage_root = storage_root
        self.extensions = extensions

        self.stop_ = False

        super(SynchronizationThread, self).__init__()
        self.name = "SynchronizationThread"

    def run(self):
        # TODO should those be pathlib objects or plain strings
        while not self.stop_:
            # TODO error handling
            startup_information = self.server_queue.get()
            # breaks to enable sort of immediate return
            # dont know yet how to perform immediate thread teardown in python
            if self.stop_:
                break
            first_new = self.client_queue.get()
            if self.stop_:
                break

            last_saved, stage_state = startup_information
            SyncProcessor.SyncProcessor(
                queue_view=self.stage_queue,
                extensions=self.extensions,
                storage_root=self.storage_root,
                staged_files=stage_state
            ).update_queue(last_saved, first_new)

    def stop(self):
        self.stop_ = True
