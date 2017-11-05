from . import ReceiverProcessor
import threading


class ReceiverService(object):
    """
    Serwis odpowiedzialny za odbieranie danych o nowopowstalych plikach od providera.

    Schemat dzialania:
    1. Proba polaczenia z socketem wystawionym przez druga strone
    2. Odbieranie danych z bufora tcp (tzw. strumienia)
    3. Rozdzielanie danych ze strumienia
    4. Zweryfikowanie istnienia plikow na podstawie skonfigurowanych rozszerzen
    5. Dodanie plikow do kolejki

    Pojecia:
    Staged/Announced file - plik "ogloszony" przez labview oraz faktycznie istniejacy na dysku
                            ktory nie zostal jeszcze zapisany na serwerze. W praktyce kazdy plik w kolejce.
    Provider - program obslugujacy stanowisko pomiarowe, rozglaszajacy stworzone pliki z pomiarami.
               Pliki rozglaszane sa poprzez socket (tcp) o zadanym adresie.

    Informacje dodatkowe:
    * Po zerwaniu polaczenia przez druga strone serwis wykonuje proby ponownego nawiazania co okreslony interwal
    * Kolejka musi byc w stanie przechowac swoj stan w przypadku naglego zakonczenia
      dzialania programu (np. odciecie zasilania)
    """
    def __init__(self):
        pass