
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
