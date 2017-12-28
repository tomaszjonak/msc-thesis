Repozytorium zawiera zarowno kod klienta, serwera oraz aplikacji symulujacej stanowisko pomiarowe

## Zgrubny schemat dzialania

Aplikacje komunikuja sie miedzy soba za pomoca protokolu tcp, maja zaszyte "na sztywno" podstawowe wartosci realizujace komunikacje
po interfejsie lokalnym. Uproszczony schemat:

data provider <- 50321 -> client <- 50123 -> server

Gdzie liczby na polaczeniach to numery portow

Provider oraz server sa aplikacjami pasywnymi, czekaja na polaczenie ktore inicjuje klient

### Lokalizacje na dysku

Do poprawnego dzialania klient oraz data provider potrzebuja miec ustawiony tzw storage_root na ten sam katalog, inaczej klient nie znajdzie plikow do wyslania

Storage root serwera musi byc ustawiony na inny katalog (inaczej nadpisze pliki) i odwzoruje on strukture katalogow ktora znajduje sie na kliencie.

## Konfiguracja data providera (aplikacja wysylajaca juz istniejace pliki)

Katalog roboczy: glowny katalog repozytorium
$ python sync/labview_sim/data_provider.py -hs <host> -p <port> -s <sciezka do katalogu z pomiarami> -e <rozszerzenia plikow rozdzielone spacjami>

Aplikacja przeszukuje podany katalog rekurencyjnie, znajdujac wszystkie pliki o podanych rozszerzeniach, sortuje je (z tego powodu musza miec schemat nazewnicta generowany z labview)
a nastepnie wysyla zgodnie z zadanym trybem. Sciezki plikow interpretowane sa relatywnie do katalogu podanego w parametrze '-s'.

Aplikacja posiada dwa tryby:
    interkatywny (domyslny)
    automatyczny

W pierwszym z nich aby wyslac informacje o pojawieniu sie nowego pliku do klienta nalezy wcisnac enter, mozna rowniez pominac plik - w tym celu trzeba wpisac dowolny znak przed enterem. Tryb interaktywny zacznie pracowac w momencie gdy zostanie nawiazane polaczeni z klientem.
Tryb automatyczny wymaga uzycia dodatkowej flagi '-sl <interwal w sekundach>', aplikacja rozglasza wtedy nowy plik co zadany interwal. Mozna rowniez podac dodatkowy parametr -sk (skip) ktory sprawia ze aplikacja ignoruje n pierwszych wpisow, uzyteczne do zaobserwowania dzialania synchronizacji.

Istnieje rowniez aplikacja generujaca losowe dane jednak przy uzyciu kompresji nie wydaje sie zbyt uzyteczna.

## Konfiguracja servera

Katalog roboczy: glowny katalog repozytorium
$ ./server.py
Bez parametrow server bedzie nasluchiwal na adresie 127.0.0.1:50123, uruchomienie go utworzy rowniez plik state_storage/server.cache (pozostalosc po poprzednim podejsciu do synchronizacji)
Opcje mozna modyfikowac albo podajac plik konfiguracyjny albo ustawiajac wartosci z konsoli

Struktura pliku konfiguracyjnego (format json, sa to rowniez wartosci domyslne zaszyte w kodzie)
{
  "host": "127.0.0.1",
  "port": 50123,
  "cache_path": "state_storage/server.cache",
  "storage_root": "state_storage/server_storage_root"
}

Zakladajac ze plik konfiguracyjny znajduje sie w tym samym katalogu i nazywa sie server.json odpalamy server komenda
./server.py -c server.json

Nadpisac opcje mozna za pomoca nazw
./server.py -o host 192.168.1.100

Opcje nadpisane z konsoli maja wyzszy priorytet niz podane w konfiguracji, jesli podamy kilkukrotnie ten sam klucz opcji (np host) ostatnia wartosc zostanie uzyta

## Konfiguracja klienta

Katalog roboczy: glowny katalog repozytorium
Sposob konfiguracji analogicznie do serwera, domyslnie sprobouje sie polaczyc na adresy 127.0.0.1:50123 oraz 127.0.0.1:50321, jesli to sie nie uda bedzie ponawial polaczeni co zadany interwal (paramter retry_time w konfiguracji)

Struktura pliku konfiguracyjnego (wartosci domyslne):

{
  "server": {
    "host": "127.0.0.1",
    "port": 50123
  },
  "provider": {
    "host": "127.0.0.1",
    "port": 50321,
    "extensions": [
      "lvm",
      "avi"
    ],
    "retry_time": 30,
    "separator": "\n"
  },
  "storage_root": "client_storage",
  "stage_queue_path": "state_storage/stage.queue",
  "cache_path": "state_storage/client.cache"
}

Zmiana wartosci za pomoca opcji w przypadku zagniezdzonym:
$ ./client.py -o server.host 192.168.0.1 -o storage_root /sciezka/do/katalogu/pomiarow

TODO: szerszy opis konfiguracji klienta
