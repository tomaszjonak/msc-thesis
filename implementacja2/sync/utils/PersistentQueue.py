import abc
import sqlite3
import time


class Queue(abc.ABC):
    """
    Interfejs kolejki odpornej na przerwanie dzialania programu.

    Definicje:
    Najnowszy plik - ostatni stworzony przez oprogramowanie pomiarowe

    Informacje dodatkowe:
    * Proponowany jest schemat FIFO (ang. first in first out).
    * W przypadku synchronizacji mozna nadac priorytet najnowszym plikom.
    * Kolejka wymaga jedynie interfejsow blokujacych (synchronicznych)
    * interfejs nie jest przewidziany do zastosowan wielowatkowych w rozumieniu ogolnym.
      W jezyku python kwestia ta nie jest do konca jednoznaczna (patrz GIL - Global Interpreter Lock)
    """

    @abc.abstractmethod
    def put(self, element):
        """
        Dodaje element do kolejki
        :param element: poki co brak ograniczen dotyczacych typu
        """
        pass

    @abc.abstractmethod
    def get(self):
        """
        Zwraca ostatni element z kolejki
        :return:
        """
        pass

    @abc.abstractmethod
    def pop(self, element):
        """
        Usuwa zadany element z kolejki o ile znajduje sie w kolejce
        :return:
        """
        pass

    @abc.abstractmethod
    def len(self):
        """
        :return: Liczba elementow w kolejce
        """
        pass

    @abc.abstractmethod
    def get_all(self):
        """
        :return: Lista elementow obecnie znajdujacych sie w kolejce
        """
        pass


class SqliteQueue(Queue):
    """
    Implementacja kolejki dyskowej z wykorzystaniem bazy danych sqlite. Warto zwrocic uwage ze get zwraca str(element)
    """

    ORDER_MAP = {
        'query': r'SELECT element FROM queue LIMIT 1',
        'LIFO': r'SELECT element from queue ORDER BY queue.timestamp DESC LIMIT 1',
        'FIFO': r'SELECT element from queue ORDER BY queue.timestamp ASC LIMIT 1'
    }

    def __init__(self, path: str, interval: float=0.5, order='query'):
        self.path = path
        self.interval = interval
        self.connection = sqlite3.connect(self.path, check_same_thread=False)

        self.get_impl = self.ORDER_MAP[order]

        curs = self.connection.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='queue'""")
        if not curs.fetchone():
            self._setup_scheme()

    def set_order(self, order):
        self.get_impl = self.ORDER_MAP[order]

    def _setup_scheme(self):
        # TODO test queue size trends on working system
        # TODO check whether indexing by timestamp gives any performance difference
        self.connection.execute(r'CREATE TABLE queue (timestamp DATETIME, element TEXT)')

    def put(self, element):
        try:
            value = str(element)
        except:
            # TODO czy bawic sie w picklowanie obiektow pythonowych?
            raise RuntimeError('put argument has to be convertible to string')

        # sqlite expects list of values as second parameter, if it happens
        # that string is passed it will be treated as array of characters (silly stuff)
        with self.connection:
            self.connection.execute("""INSERT INTO queue VALUES (strftime('%Y-%m-%d %H:%M:%f', 'now'),?)""", (value,))

    def get(self, wait_for_value=True, timeout=None):
        return self.waiting_get(timeout=timeout) if wait_for_value else self.instant_get()

    def get_all(self):
        result = self.connection.execute("""SELECT element FROM queue""").fetchall()
        return [x for (x,) in result]

    def waiting_get(self, timeout=None):
        """
        :return: str - element z kolejki (w zaleznosci od paramteru order)
        """
        record = self.connection.execute(self.get_impl).fetchone()

        time_passed = 0
        while not record:
            time.sleep(self.interval)
            time_passed += self.interval

            if timeout and time_passed >= timeout:
                raise TimeoutError()

            record = self.connection.execute(self.get_impl).fetchone()

        return record[0]

    def instant_get(self):
        """
        :return: value if any present in queue else none
        """
        record = self.connection.execute(self.get_impl).fetchone()
        return record[0] if record else None

    def pop(self, element):
        """
        Jesli pojawi sie wiecej niz jeden element o takiej samej wartosci wszystkie zostana usuniete.
        Bazuje to na zalozeniu ze soft pomiarowy daje kolejnym plikom unikalne nazwy
        """
        self.connection.execute(r'DELETE FROM queue where element=?', (element,))
        self.connection.commit()

    def len(self):
        record = self.connection.execute(r'SELECT count(*) from queue').fetchone()
        return record[0]

    def __del__(self):
        self.connection.close()


DefaultQueue = SqliteQueue
