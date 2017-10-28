import abc


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
