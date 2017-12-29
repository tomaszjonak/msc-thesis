import abc


class StreamTransofrmation(abc.ABC):
    """
    Klasa definiujaca interfejs do przetworzenia strumienia w trakcie dzialania programu.
    Przykladem takiej operacji jest kompresja, dekompresja, liczenie checksumy.

    W miejsce to mozna rowniez wpiac dowolny skrypt ktory przyjmuje dane na wejscie standardowe,
    przetwarza je a nastepnie zwraca wynik na wyjscie standardowe - analogiczne do interfejsu potokow (pipe)
    w bashu.

    Przyklad pogladowy z basha:
    cat data.csv | cut -d',' -f 1 | netcat 127.0.0.1 4321
    cat data.csv          - strumien wejsciowy
    cut -d',' -f 1        - transformacja (wybranie tylko pierwszej kolumny z kazdego wiersza)
    netcat 127.0.0.1 4321 - odbiorca (strumien wyjsciowy)

    Interfejs ten moze rowniez sluzyc do wykonywania operacji pobocznych (takich jak liczenie sumy kontrolnej)
    ktore nie modyfikuje strumiena jednak potrzebuje przetworzyc wszystkie informacje ktore sie na niego skladaja
    """

    @abc.abstractmethod
    def transform(self, data_chunk: bytes):
        """
        Dokonuje transformacji na danym fragmencie danych, jesli transformacja moze zwracac dane czesciami
        zwraca przetransformowany kawalek danych
        """
        pass

    @abc.abstractmethod
    def flush(self):
        """
        Konczy transformacje zwracajac dane pozostale w buforach danej transformacji (o ile takowe istnieja)
        """
        pass
