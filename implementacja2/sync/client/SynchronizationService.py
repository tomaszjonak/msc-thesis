import threading


class SynchronizationService(object):
    pass


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
    def __init__(self, server_queue, client_queue, queue_view, storage_root):
        self.server_queue = server_queue
        self.client_queue = client_queue
        self.stage_queue = queue_view

        super(SynchronizationThread, self).__init__()

    def run(self):
        # TODO should those be pathlib objects or plain strings
        startup_information = self.server_queue.get()
        first_new = self.client_queue.get()

