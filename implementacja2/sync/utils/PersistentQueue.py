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


class SqliteQueue(Queue):
    """
    Implementacja kolejki dyskowej z wykorzystaniem bazy danych sqlite. Warto zwrocic uwage ze get zwraca str(element)
    """
    def __init__(self, path: str, interval: float=0.05):
        self.path = path
        self.interval = interval
        self.connection = sqlite3.connect(self.path, check_same_thread=False)

        curs = self.connection.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='queue'""")
        if not curs.fetchone():
            self._setup_scheme()

    def _setup_scheme(self):
        self.connection.execute(r'CREATE TABLE queue (timestamp text, element text)')
        self.connection.commit()

    def put(self, element):
        try:
            value = str(element)
        except:
            # TODO czy bawic sie w picklowanie obiektow pythonowych?
            raise RuntimeError('put argument has to be convertible to string')

        # sqlite expects list of values as second parameter, if it happens
        # that string is passed it will be treated as array of characters (silly stuff)
        self.connection.execute(r'INSERT INTO queue VALUES (DATETIME(),?)', (value,))
        self.connection.commit()

    def get(self, wait_for_value=True):
        return self.waiting_get() if wait_for_value else self.instant_get()

    def waiting_get(self):
        """
        :return: str - ostatni element z kolejki
        """
        curs = self.connection.execute(r'SELECT element FROM queue LIMIT 1')
        record = curs.fetchone()
        # TODO zmienic na lock
        while not record:
            curs = self.connection.execute(r'SELECT element FROM queue LIMIT 1')
            record = curs.fetchone()
            time.sleep(self.interval)

        return record[0]

    def instant_get(self):
        """
        :return: value if any present in queue else none
        """
        curs = self.connection.execute(r'SELECT element FROM queue LIMIT 1')
        record = curs.fetchone()
        return record[0] if record else None

    def pop(self, element):
        """
        Jesli pojawi sie wiecej niz jeden element o takiej samej wartosci wszystkie zostana usuniete.
        Bazuje to na zalozeniu ze soft pomiarowy daje kolejnym plikom unikalne nazwy
        """
        self.connection.execute(r'DELETE FROM queue where element=?', (element,))
        self.connection.commit()

    def len(self):
        curs = self.connection.execute(r'SELECT count(*) from queue')
        record = curs.fetchone()
        return record[0]

    def __del__(self):
        self.connection.close()


DefaultQueue = SqliteQueue
