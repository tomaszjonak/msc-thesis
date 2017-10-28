

class SenderService(object):
    """
    Serwis odpowiedzialny za komunikacje (uzywajac okreslonego protokolu) z serwerem

    Schemat dzialania:
    1.  Nawiazanie polaczenia z serwerem
    2.  Odebranie informacji o najnowszym pliku zapisanym na serwerze (patrz pojecia)
    3.  (opcjonalne) uzupelnienie koljeki o pliki ktore zostaly stworzone ale nie rozgloszone (synchronizacja)
    4.  Pobieranie plikow z kolejki
    4.5 (opcjonalne) kompresja pliku
    5.  Przesyl zgodnie z zadanym protokolem
    6.  Usuniecie plikow z kolejki po otrzymaniu potwierdzenia zapisania przez serwer

    Pojecia:
    Najnowszy plik zapisany na serwerze - porzadek plikow ustala data zawarta w nazwie pliku
    Synchronizacja - obsluzenie nieplanowanego bledu w dzialaniu ktoregos z komponentow

    Dodatkowe informacje:
    * Serwis ponawia polaczenie analogicznie do odbierajcego z labview
    * Schemat kompresji jest wymienny, istnieje mozliwosc wyboru schematu kompresji w zaleznosci od rozszerzenia pliku
    """
